"""Pure-Python scene loader for the UE simulation runtime.

This module is intentionally free of ``import unreal`` so it can be:
    * unit-tested outside the Unreal Editor process,
    * imported by tooling that runs in CPython.

The actual UE-side logic (FBX import, ControlRig generation, actor spawning)
lives in ``benchmark.senior_care.base.ue_script``.

The YAML file consumed here is the same one the MuJoCo runtime reads
(``config/demo.yaml``), so both back-ends stay in sync.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml


# Locate the workspace root (``python/``) and repo root (``roboLab/``) so that
# relative paths in the YAML can be resolved without relying on cwd.
_THIS_FILE = Path(__file__).resolve()
WORKSPACE_ROOT = _THIS_FILE.parents[4]   # python/
REPO_ROOT = _THIS_FILE.parents[5]        # roboLab/


# ---------------------------------------------------------------------------
# Joint -> bone aliasing
# ---------------------------------------------------------------------------

# SMPL-X joint short tokens (used in demo.yaml's ``joint_order``) -> bone names
# present in the SMPL-X FBX skeleton produced by ``convert_smplx.sh``.
SMPLX_JOINT_ALIAS: dict[str, str] = {
    "neck": "neck",
    "l_shoulder": "left_shoulder",
    "r_shoulder": "right_shoulder",
    "l_elbow": "left_elbow",
    "r_elbow": "right_elbow",
    "l_wrist": "left_wrist",
    "r_wrist": "right_wrist",
    "l_knee": "left_knee",
    "r_knee": "right_knee",
    "l_ankle": "left_ankle",
    "r_ankle": "right_ankle",
    "l_hip": "left_hip",
    "r_hip": "right_hip",
}


def bone_name_for_joint(joint_name: str, mujoco_model_path: str | Path | None) -> str:
    """Resolve a YAML joint token to a *bone search token*.

    The token returned here is **not** required to equal the actual FBX
    bone name -- the loader does substring-based fuzzy matching against
    the live skeleton (URDF2FBX exports bones with names like
    ``panda_joint1_revolute_bone`` / ``panda_hand_joint_fixed_bone``,
    whose exact suffix depends on the joint type). All we need is a
    token that is *unique* and a *substring* of exactly one FBX bone.

    * Franka URDF: ``panda_jointN`` itself is unique among bone names
      (each shows up exactly once as ``panda_jointN_revolute_bone``).
      Same for ``panda_hand_joint`` and ``panda_finger_jointN``.
    * SMPL-X: short tokens like ``r_elbow`` are not unique substrings,
      so we expand them to the canonical ``right_elbow``-style names.
    * Fallback: return the joint name verbatim.
    """
    if joint_name.startswith("panda_") and "joint" in joint_name:
        return joint_name
    if joint_name in SMPLX_JOINT_ALIAS:
        return SMPLX_JOINT_ALIAS[joint_name]

    model_hint = str(mujoco_model_path or "").lower()
    if "smplx" in model_hint and joint_name in SMPLX_JOINT_ALIAS:
        return SMPLX_JOINT_ALIAS[joint_name]

    return joint_name


# ---------------------------------------------------------------------------
# Root pose helpers
# ---------------------------------------------------------------------------


def _to_xyz(values: Iterable[float] | None, default: tuple[float, float, float]) -> tuple[float, float, float]:
    if values is None:
        return default
    items = [float(v) for v in values]
    if len(items) != 3:
        raise ValueError(f"expected 3 values, got {len(items)}: {items}")
    return items[0], items[1], items[2]


def _to_quat_wxyz(values: Iterable[float] | None) -> tuple[float, float, float, float]:
    """Normalise the YAML's orientation entry to (w, x, y, z).

    The MuJoCo configs in this repo are inconsistent: some use (w, x, y, z)
    (e.g. the franka asset) while others use (x, y, z, w) (e.g. simpl_neutral
    where ``orientation: [0.0, 0.0, 0.0, 1.0]`` is the identity in xyzw).

    We assume MuJoCo's native convention (w, x, y, z) by default, but if the
    first element looks non-unit and the last is exactly 1, treat as xyzw.
    """
    if values is None:
        return 1.0, 0.0, 0.0, 0.0
    items = [float(v) for v in values]
    if len(items) != 4:
        raise ValueError(f"expected 4 quaternion values, got {len(items)}: {items}")
    a, b, c, d = items
    if abs(a) < 1e-6 and abs(d - 1.0) < 1e-6:
        return d, a, b, c
    return a, b, c, d


# ---------------------------------------------------------------------------
# Look-at helpers (used by the optional ``look_at:`` field on cameras)
# ---------------------------------------------------------------------------


def _quat_ue_look_rotation(
    forward: tuple[float, float, float],
    up: tuple[float, float, float] = (0.0, 0.0, 1.0),
) -> tuple[float, float, float, float]:
    """Build the UE quaternion that rotates local +X to point at ``forward``.

    UE convention: a camera at identity rotation looks down +X, with +Y to
    the right and +Z up. We construct an orthonormal basis from the desired
    forward and an up hint, then convert the resulting rotation matrix to
    a quaternion (w, x, y, z).

    The arithmetic is done in *raw* coordinates (i.e. whatever frame the
    YAML uses for ``position`` / ``look_at``), so the caller does not need
    to care about MuJoCo<->UE handedness here -- the YAML position pipeline
    already pastes raw numbers into UE world space verbatim.
    """
    fx, fy, fz = forward
    fl = math.sqrt(fx * fx + fy * fy + fz * fz)
    if fl < 1e-9:
        return (1.0, 0.0, 0.0, 0.0)
    fx, fy, fz = fx / fl, fy / fl, fz / fl

    ux, uy, uz = up
    # UE world is left-handed (X forward, Y right, Z up). For a basis where
    # local +X = forward, +Y = right, +Z = up to be a *proper* rotation
    # (det = +1) in standard right-hand-rule cross-product math, the right
    # axis must come from ``right = up x forward``. The opposite order
    # ``forward x up`` builds a det = -1 reflection matrix and the
    # quaternion conversion silently breaks.
    rx = uy * fz - uz * fy
    ry = uz * fx - ux * fz
    rz = ux * fy - uy * fx
    rl = math.sqrt(rx * rx + ry * ry + rz * rz)
    if rl < 1e-6:
        # forward parallel to up_hint - pick an arbitrary up.
        ux, uy, uz = 1.0, 0.0, 0.0
        rx = uy * fz - uz * fy
        ry = uz * fx - ux * fz
        rz = ux * fy - uy * fx
        rl = math.sqrt(rx * rx + ry * ry + rz * rz) or 1.0
    rx, ry, rz = rx / rl, ry / rl, rz / rl

    # actual_up = forward x right (consistent with the LH convention above).
    ux2 = fy * rz - fz * ry
    uy2 = fz * rx - fx * rz
    uz2 = fx * ry - fy * rx

    # Rotation matrix R with COLUMNS = (forward, right, actual_up), so
    # R * (1,0,0) = forward, R * (0,1,0) = right, R * (0,0,1) = up.
    m00, m01, m02 = fx, rx, ux2
    m10, m11, m12 = fy, ry, uy2
    m20, m21, m22 = fz, rz, uz2

    # Standard Shoemake quaternion-from-matrix (column-vector convention).
    tr = m00 + m11 + m22
    if tr > 0.0:
        s = math.sqrt(tr + 1.0) * 2.0
        qw = 0.25 * s
        qx = (m21 - m12) / s
        qy = (m02 - m20) / s
        qz = (m10 - m01) / s
    elif (m00 > m11) and (m00 > m22):
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2.0
        qw = (m21 - m12) / s
        qx = 0.25 * s
        qy = (m01 + m10) / s
        qz = (m02 + m20) / s
    elif m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2.0
        qw = (m02 - m20) / s
        qx = (m01 + m10) / s
        qy = 0.25 * s
        qz = (m12 + m21) / s
    else:
        s = math.sqrt(1.0 + m22 - m00 - m11) * 2.0
        qw = (m10 - m01) / s
        qx = (m02 + m20) / s
        qy = (m12 + m21) / s
        qz = 0.25 * s

    return (qw, qx, qy, qz)


def _resolve_look_at(
    value: Any,
    asset_positions_m: Mapping[str, tuple[float, float, float]],
) -> tuple[float, float, float]:
    """Resolve a YAML ``look_at`` entry to a single (x, y, z) world point.

    Accepted forms:

    * ``[x, y, z]`` -- explicit world point (metres, same frame as the
      camera ``position`` field).
    * ``"<asset_name>"`` -- the root position of that asset.
    * ``["<asset_a>", "<asset_b>", ...]`` -- centroid of the listed
      assets' root positions.
    * Mixed lists (string + numbers) raise ``ValueError``.

    ``asset_positions_m`` maps asset name -> (x, y, z) metres.
    """
    if isinstance(value, str):
        try:
            return asset_positions_m[value]
        except KeyError as exc:
            raise KeyError(
                f"camera look_at='{value}' refers to an unknown asset; "
                f"known assets: {sorted(asset_positions_m)}"
            ) from exc

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        items = list(value)
        if not items:
            raise ValueError("look_at list is empty")
        if all(isinstance(v, (int, float)) for v in items):
            return _to_xyz(items, (0.0, 0.0, 0.0))
        if all(isinstance(v, str) for v in items):
            try:
                points = [asset_positions_m[name] for name in items]
            except KeyError as exc:
                raise KeyError(
                    f"camera look_at refers to unknown asset {exc!s}; "
                    f"known assets: {sorted(asset_positions_m)}"
                ) from exc
            n = float(len(points))
            return (
                sum(p[0] for p in points) / n,
                sum(p[1] for p in points) / n,
                sum(p[2] for p in points) / n,
            )
        raise ValueError(
            f"look_at list must be either 3 numbers or all asset-name "
            f"strings, got mixed: {items}"
        )

    raise ValueError(f"unsupported look_at value: {value!r}")


def parse_ue_root(asset_config: Mapping[str, Any]) -> tuple[tuple[float, float, float], tuple[float, float, float, float], float]:
    """Return ``(position_cm, quaternion_wxyz, scale)`` for UE placement.

    * MuJoCo positions are in **meters**; UE is in **centimeters** so we
      multiply by 100.
    * The ``scale`` value in the YAML is a *mesh-scale* hint (e.g. SMPL-X is
      authored in meters, so 100 must be applied to the actor's transform
      scale to display correctly inside UE).
    """
    root = asset_config.get("root", {})
    pos_m: tuple[float, float, float]
    quat_wxyz: tuple[float, float, float, float]

    if isinstance(root, list):
        pos_m = (0.0, 0.0, 0.0)
        quat_wxyz = (1.0, 0.0, 0.0, 0.0)
        for entry in root:
            if not isinstance(entry, dict):
                continue
            if "position" in entry:
                pos_m = _to_xyz(entry["position"], pos_m)
            if "orientation" in entry:
                quat_wxyz = _to_quat_wxyz(entry["orientation"])
            elif "rotation" in entry:
                quat_wxyz = _to_quat_wxyz(entry["rotation"])
    elif isinstance(root, dict):
        pos_m = _to_xyz(root.get("position"), (0.0, 0.0, 0.0))
        quat_wxyz = _to_quat_wxyz(root.get("orientation", root.get("rotation")))
    else:
        pos_m = (0.0, 0.0, 0.0)
        quat_wxyz = (1.0, 0.0, 0.0, 0.0)

    pos_cm = (pos_m[0] * 100.0, pos_m[1] * 100.0, pos_m[2] * 100.0)
    scale = float(asset_config.get("scale", 1.0))
    return pos_cm, quat_wxyz, scale


# ---------------------------------------------------------------------------
# Spec / scene dataclasses
# ---------------------------------------------------------------------------


@dataclass
class UeCameraSpec:
    """One camera entry from the ``cameras:`` block of demo.yaml.

    Positions are stored in **metres** (MuJoCo convention); use the
    ``position_cm`` property when positioning UE actors (cm).

    ``look_at_target_m`` is populated when the YAML used the optional
    ``look_at:`` field (either as ``[x, y, z]`` or as one or more asset
    names). It is purely informational -- the actual rotation is already
    baked into ``orientation_wxyz``.
    """

    name: str
    position_m: tuple[float, float, float]
    orientation_wxyz: tuple[float, float, float, float]
    width: int = 640
    height: int = 480
    fov: float = 90.0  # horizontal FOV in degrees
    look_at_target_m: tuple[float, float, float] | None = None

    @property
    def position_cm(self) -> tuple[float, float, float]:
        """Camera centre in UE world space (centimetres)."""
        return (
            self.position_m[0] * 100.0,
            self.position_m[1] * 100.0,
            self.position_m[2] * 100.0,
        )


@dataclass
class UeAssetSpec:
    """One asset entry from ``demo.yaml`` translated for the UE runtime."""

    name: str
    ue_model_path: Path
    mujoco_model_path: Path | None
    frame: str
    fix_base: bool
    disable_gravity: bool
    scale: float
    root_position_cm: tuple[float, float, float]
    root_rotation_wxyz: tuple[float, float, float, float]
    selected_joints: list[str]
    joint_initial_positions: list[float]
    behavior_of_unspecified: str
    joint_order: list[str] = field(default_factory=list)
    raw: Mapping[str, Any] = field(default_factory=dict)
    #: Optional ``/Game/...`` path to a ``MaterialInterface`` for instance overrides.
    ue_material_path: str | None = None
    #: Optional linear RGBA in 0..1 for dynamic material tint (see ``ue_script``).
    base_color: tuple[float, float, float, float] | None = None
    #: When True, skip Python material overrides and keep FBX-imported materials.
    use_imported_materials: bool = False

    @property
    def drivable_bones(self) -> list[str]:
        """Bones this asset wants individually controllable from Python.

        We always include the bones referenced by ``selected_joints``. When the
        selection is empty (typical for the SMPL-X human, where the YAML lists
        none) we fall back to the bones referenced by ``joint_order`` so the
        runtime rig still exposes the joints documented in the config.
        """
        names = list(self.selected_joints) or list(self.joint_order)
        bones: list[str] = []
        seen: set[str] = set()
        for joint in names:
            bone = bone_name_for_joint(joint, self.mujoco_model_path)
            if bone in seen:
                continue
            seen.add(bone)
            bones.append(bone)
        return bones

    def bone_for_joint(self, joint_name: str) -> str:
        return bone_name_for_joint(joint_name, self.mujoco_model_path)


@dataclass
class UeScene:
    yaml_path: Path
    raw: Mapping[str, Any]
    specs: list[UeAssetSpec]
    cameras: list[UeCameraSpec] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "UeScene":
        path = _resolve_path(Path(yaml_path))
        # Force UTF-8: UE's bundled Python 3.9 on Linux defaults to ASCII for
        # text reads, which fails on YAMLs that contain Chinese comments.
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        specs = [
            _spec_from_asset_config(asset_cfg, anchor=path.parent)
            for asset_cfg in raw.get("assets", [])
        ]
        # Build the lookup table cameras need to resolve a ``look_at: <asset>``
        # reference to a world-space (x, y, z) point in metres.
        asset_positions_m: dict[str, tuple[float, float, float]] = {
            spec.name: (
                spec.root_position_cm[0] / 100.0,
                spec.root_position_cm[1] / 100.0,
                spec.root_position_cm[2] / 100.0,
            )
            for spec in specs
        }
        cameras = [
            _camera_spec_from_config(cam_cfg, asset_positions_m=asset_positions_m)
            for cam_cfg in raw.get("cameras", [])
        ]
        return cls(yaml_path=path, raw=raw, specs=specs, cameras=cameras)

    def find(self, name: str) -> UeAssetSpec:
        for spec in self.specs:
            if spec.name == name:
                return spec
        raise KeyError(f"Asset '{name}' not present in {self.yaml_path}")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _spec_from_asset_config(asset_cfg: Mapping[str, Any], *, anchor: Path) -> UeAssetSpec:
    name = str(asset_cfg.get("name") or "asset")

    ue_model_raw = asset_cfg.get("ue_model")
    if ue_model_raw is None and "uue_model" in asset_cfg:
        # Tolerate a known typo seen in demo.yaml ('uue_model').
        ue_model_raw = asset_cfg["uue_model"]
    if ue_model_raw is None:
        raise KeyError(
            f"Asset '{name}' is missing 'ue_model' (path to the FBX file) in the YAML."
        )
    ue_model_path = _resolve_path(Path(ue_model_raw), extra_anchors=[anchor])

    mujoco_model_raw = asset_cfg.get("mujoco_model")
    mujoco_model_path: Path | None = None
    if mujoco_model_raw:
        try:
            mujoco_model_path = _resolve_path(Path(mujoco_model_raw), extra_anchors=[anchor])
        except FileNotFoundError:
            mujoco_model_path = Path(mujoco_model_raw)  # keep as-is just for hinting

    frame = str(asset_cfg.get("frame") or "")
    fix_base = bool(asset_cfg.get("fix_base", False))
    disable_gravity = bool(asset_cfg.get("disable_gravity", False))
    pos_cm, quat_wxyz, scale = parse_ue_root(asset_cfg)

    state_cfg = asset_cfg.get("state") or {}
    position_cfg = state_cfg.get("position") or {}
    joint_initial_positions = [float(v) for v in (position_cfg.get("initial") or [])]
    joint_order = [str(j) for j in (position_cfg.get("joint_order") or [])]

    action_cfg = asset_cfg.get("action") or {}
    selected_joints = [str(j) for j in (action_cfg.get("selected_joints") or [])]
    behavior = str(action_cfg.get("behavior_of_unspecified", "free")).lower()

    ue_material_path, base_color, use_imported_materials = parse_render_options(
        asset_cfg
    )

    return UeAssetSpec(
        name=name,
        ue_model_path=ue_model_path,
        mujoco_model_path=mujoco_model_path,
        frame=frame,
        fix_base=fix_base,
        disable_gravity=disable_gravity,
        scale=scale,
        root_position_cm=pos_cm,
        root_rotation_wxyz=quat_wxyz,
        selected_joints=selected_joints,
        joint_initial_positions=joint_initial_positions,
        behavior_of_unspecified=behavior,
        joint_order=joint_order,
        raw=asset_cfg,
        ue_material_path=ue_material_path,
        base_color=base_color,
        use_imported_materials=use_imported_materials,
    )


def parse_render_options(
    asset_cfg: Mapping[str, Any],
) -> tuple[str | None, tuple[float, float, float, float] | None, bool]:
    """Parse optional ``ue_material``, ``base_color``, ``use_imported_materials``."""
    um_raw = asset_cfg.get("ue_material")
    ue_material_path = str(um_raw).strip() if um_raw else None
    if ue_material_path == "":
        ue_material_path = None

    base_color: tuple[float, float, float, float] | None = None
    bc = asset_cfg.get("base_color")
    if bc is not None:
        vals = [float(v) for v in bc]
        if len(vals) == 3:
            base_color = (vals[0], vals[1], vals[2], 1.0)
        elif len(vals) == 4:
            base_color = (vals[0], vals[1], vals[2], vals[3])
        else:
            raise ValueError(
                "base_color must be 3 or 4 floats [r,g,b] or [r,g,b,a], "
                f"got {len(vals)} value(s)"
            )

    use_imported_materials = bool(asset_cfg.get("use_imported_materials", False))

    return ue_material_path, base_color, use_imported_materials


def _camera_spec_from_config(
    cam_cfg: Mapping[str, Any],
    *,
    asset_positions_m: Mapping[str, tuple[float, float, float]] | None = None,
) -> UeCameraSpec:
    """Parse one entry from the ``cameras:`` YAML list into a :class:`UeCameraSpec`.

    Recognised optional fields:

    * ``look_at`` -- one of:
        - ``[x, y, z]`` -- explicit world point (metres, same frame as ``position``)
        - ``"<asset_name>"`` -- look at that asset's root position
        - ``["<a>", "<b>", ...]`` -- look at the centroid of those assets
      When present it overrides any ``orientation:`` field.
    * ``up`` -- 3-vector hint for the camera's "up" direction (defaults to
      world +Z).
    * ``orientation`` -- explicit (w, x, y, z) quaternion in the YAML's
      historical convention (used when ``look_at`` is absent).
    """
    name = str(cam_cfg.get("name") or "camera")
    pos_m = _to_xyz(cam_cfg.get("position"), (0.0, 0.0, 0.0))
    width = int(cam_cfg.get("width", 640))
    height = int(cam_cfg.get("height", 480))
    fov = float(cam_cfg.get("fov", 90.0))

    look_at_raw = cam_cfg.get("look_at")
    look_at_target_m: tuple[float, float, float] | None = None
    if look_at_raw is not None:
        target_m = _resolve_look_at(look_at_raw, asset_positions_m or {})
        look_at_target_m = target_m
        up_m = _to_xyz(cam_cfg.get("up"), (0.0, 0.0, 1.0))
        # The position pipeline pastes raw YAML numbers verbatim into UE
        # world space (just unit-converted, see UeCameraSpec.position_cm).
        # Compute the look-at rotation in that same raw frame so a UE
        # camera placed at ``position`` with this rotation has its forward
        # axis pointing at ``look_at``.
        forward = (
            target_m[0] - pos_m[0],
            target_m[1] - pos_m[1],
            target_m[2] - pos_m[2],
        )
        q_ue = _quat_ue_look_rotation(forward, up_m)
        # The UE-side converter (`_quat_wxyz_to_unreal_rotator`) negates the
        # ``y`` component on its way to UE for MuJoCo-frame quaternions.
        # Pre-negate ``y`` here so the round-trip yields the UE quaternion
        # we just computed.
        ori_wxyz = (q_ue[0], q_ue[1], -q_ue[2], q_ue[3])
    else:
        ori_wxyz = _to_quat_wxyz(cam_cfg.get("orientation"))

    return UeCameraSpec(
        name=name,
        position_m=pos_m,
        orientation_wxyz=ori_wxyz,
        width=width,
        height=height,
        fov=fov,
        look_at_target_m=look_at_target_m,
    )


def _resolve_path(raw_path: Path, *, extra_anchors: list[Path] | None = None) -> Path:
    """Resolve YAML-relative paths against the YAML directory, ``python/``,
    and the repo root."""
    if raw_path.is_absolute() and raw_path.exists():
        return raw_path

    anchors: list[Path] = []
    if extra_anchors:
        anchors.extend(extra_anchors)
    anchors.extend([WORKSPACE_ROOT, REPO_ROOT])

    for anchor in anchors:
        candidate = anchor / raw_path
        if candidate.exists():
            return candidate.resolve()

    raise FileNotFoundError(
        f"Path not found: {raw_path} (searched {[str(a) for a in anchors]})"
    )


__all__ = [
    "SMPLX_JOINT_ALIAS",
    "UeAssetSpec",
    "UeCameraSpec",
    "UeScene",
    "bone_name_for_joint",
    "parse_render_options",
    "parse_ue_root",
]
