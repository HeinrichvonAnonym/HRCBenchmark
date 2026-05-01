from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping
import warnings

import mujoco
import yaml

_MUJOCO_MESH_SUFFIXES = {".obj", ".stl", ".msh"}


def parse_asset_root(asset_config: Mapping[str, Any]) -> tuple[list[float], list[float]]:
    """Return (position_xyz, quaternion_wxyz) for MuJoCo frame placement."""
    root_config = asset_config.get("root", {})
    if isinstance(root_config, list):
        pos = [0.0, 0.0, 0.0]
        quat = [0.0, 0.0, 0.0, 1.0]
        for entry in root_config:
            if not isinstance(entry, dict):
                continue
            if "position" in entry:
                pos = [float(x) for x in entry["position"]]
            if "rotation" in entry:
                quat = [float(x) for x in entry["rotation"]]
            if "orientation" in entry:
                quat = [float(x) for x in entry["orientation"]]
        return pos, quat
    if isinstance(root_config, dict):
        pos = [float(v) for v in root_config.get("position", [0.0, 0.0, 0.0])]
        ori = root_config.get("orientation", root_config.get("rotation", [0.0, 0.0, 0.0, 1.0]))
        quat = [float(v) for v in ori]
        return pos, quat
    return [0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 1.0]


def _parse_vec3(raw: Any, default: list[float] | None = None) -> list[float]:
    if default is None:
        default = [0.0, 0.0, 0.0]
    if isinstance(raw, (list, tuple)) and len(raw) == 3:
        return [float(raw[0]), float(raw[1]), float(raw[2])]
    return [float(default[0]), float(default[1]), float(default[2])]


def attach_mujoco_asset_to_spec(
    main_spec: mujoco.MjSpec,
    asset_config: Mapping[str, Any],
    *,
    resolve_path: Callable[[str | Path], Path],
    load_asset_spec: Callable[[str | Path], mujoco.MjSpec],
) -> None:
    """Attach one MJCF/URDF subtree or one mesh geom from ``asset_config`` into ``main_spec``."""
    model_path = asset_config.get("mujoco_model") or asset_config.get("mujoco_file")
    if not model_path:
        return

    resolved = resolve_path(model_path)
    suffix = resolved.suffix.lower()
    if suffix in _MUJOCO_MESH_SUFFIXES:
        _attach_mesh_geom_to_spec(main_spec, asset_config, resolved)
        return

    if suffix == ".dae":
        # MuJoCo does not natively load Collada meshes. Ask users to export OBJ/STL/MSH instead.
        name = str(asset_config.get("name", "asset"))
        raise ValueError(
            f"scene asset '{name}' uses unsupported mesh format '{resolved.suffix}'. "
            "Export as .obj/.stl/.msh and update mujoco_file."
        )

    child_spec = load_asset_spec(model_path)
    source_has_freejoint = any(joint.type == mujoco.mjtJoint.mjJNT_FREE for joint in child_spec.joints)
    fix_base = bool(asset_config.get("fix_base", False))
    root_position, root_orientation = parse_asset_root(asset_config)

    if fix_base and source_has_freejoint:
        raise ValueError(
            f"Asset '{asset_config.get('name', '?')}' is configured as fixed-base, but its source model "
            "already contains a free joint. This basic version does not remove embedded free joints."
        )

    if (not fix_base) and (not source_has_freejoint):
        name = str(asset_config.get("name", "asset"))
        wrapper = main_spec.worldbody.add_body()
        wrapper.name = f"{name}_root_wrapper"
        wrapper.pos = root_position
        wrapper.quat = root_orientation
        wrapper.add_freejoint()
        wrapper.mass = 1e-6
        wrapper.inertia = [1e-6, 1e-6, 1e-6]
        frame = wrapper.add_frame()
    else:
        frame = main_spec.worldbody.add_frame()
        frame.pos = root_position
        frame.quat = root_orientation

    main_spec.attach(child_spec, prefix="", frame=frame)

def _attach_mesh_geom_to_spec(
    main_spec: mujoco.MjSpec,
    asset_config: Mapping[str, Any],
    mesh_path: Path,
) -> None:
    """Attach a mesh file as visual/collision geoms in worldbody."""
    name = str(asset_config.get("name", "scene_asset"))
    fix_base = bool(asset_config.get("fix_base", True))
    root_position, root_orientation = parse_asset_root(asset_config)
    visual_offset = _parse_vec3(asset_config.get("visual_offset"))
    collision_offset = _parse_vec3(asset_config.get("collision_offset"))
    enable_visual = bool(asset_config.get("visual", True))
    enable_collision = bool(asset_config.get("collision", True))
    separate_collision_visual = bool(asset_config.get("separate_collision_visual", False))

    mesh = main_spec.add_mesh()
    mesh.name = f"{name}_mesh"
    mesh.file = str(mesh_path)

    body = main_spec.worldbody.add_body()
    body.name = f"{name}_body"
    body.pos = root_position
    body.quat = root_orientation
    if not fix_base:
        body.add_freejoint()

    split_geoms = (
        separate_collision_visual
        or visual_offset != collision_offset
        or not (enable_visual and enable_collision)
    )

    if enable_visual and enable_collision and not split_geoms:
        geom = body.add_geom()
        geom.name = f"{name}_geom"
        geom.type = mujoco.mjtGeom.mjGEOM_MESH
        geom.meshname = mesh.name
        geom.pos = visual_offset
        return

    if enable_visual:
        visual_geom = body.add_geom()
        visual_geom.name = f"{name}_visual_geom"
        visual_geom.type = mujoco.mjtGeom.mjGEOM_MESH
        visual_geom.meshname = mesh.name
        visual_geom.pos = visual_offset
        visual_geom.contype = 0
        visual_geom.conaffinity = 0

    if enable_collision:
        collision_geom = body.add_geom()
        collision_geom.name = f"{name}_collision_geom"
        collision_geom.type = mujoco.mjtGeom.mjGEOM_MESH
        collision_geom.meshname = mesh.name
        collision_geom.pos = collision_offset
        if enable_visual:
            # Hide collision hull when a dedicated visual geom exists.
            collision_geom.rgba = [0.0, 0.0, 0.0, 0.0]


class MujocoScene:
    """Scene-only MuJoCo assets loaded from a dedicated YAML (props, furniture, etc.)."""

    def __init__(self, scene_path: Path, raw: dict[str, Any]) -> None:
        self.scene_path = scene_path.resolve()
        self.raw = raw

    @classmethod
    def from_yaml_path(cls, scene_path: Path) -> MujocoScene:
        resolved = scene_path.resolve()
        data = yaml.safe_load(resolved.read_text()) or {}
        return cls(scene_path=resolved, raw=data)

    def attach_into(
        self,
        main_spec: mujoco.MjSpec,
        *,
        resolve_path: Callable[[str | Path], Path],
        load_asset_spec: Callable[[str | Path], mujoco.MjSpec],
    ) -> None:
        """Attach every asset listed under ``assets`` in the scene YAML."""
        for asset_config in self.raw.get("assets", []):
            try:
                attach_mujoco_asset_to_spec(
                    main_spec,
                    asset_config,
                    resolve_path=resolve_path,
                    load_asset_spec=load_asset_spec,
                )
            except Exception as exc:
                name = str(asset_config.get("name", "unnamed_scene_asset"))
                model_path = asset_config.get("mujoco_model") or asset_config.get("mujoco_file")
                warnings.warn(
                    f"Skipping scene asset '{name}' ({model_path}): {exc}",
                    RuntimeWarning,
                )
