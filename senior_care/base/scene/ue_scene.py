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

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

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
        return cls(yaml_path=path, raw=raw, specs=specs)

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
    "UeScene",
    "bone_name_for_joint",
    "parse_ue_root",
]
