"""Make MuJoCoSkeletalActor meshes actually visible.

The diagnose_actors.py output proved that:
    * Franka has 60 placeholder material slots from URDF->FBX export
      (``Part__Feature017_001`` etc), most of which don't have a real
      shader attached, so the mesh renders as nothing.
    * SMPL-X only has WorldGridMaterial (UE's 'no-material' fallback),
      which should be visible -- but in our SM5 + no-Lumen pipeline it
      sometimes ends up not rendering either.

Fix: at the PoseableMeshComponent level, OVERRIDE every material slot
with a known-good engine default. This is a per-instance override, the
underlying SkeletalMesh asset stays untouched, and you can remove the
override later from the Details panel if you want to wire up real
materials.

Choice of default: ``/Engine/BasicShapes/BasicShapeMaterial`` -- the
plain grey shader used by the basic shapes (Cube, Sphere, etc). It's
guaranteed to exist on every UE install and renders cleanly under
Movable Skylight + DirectionalLight.

Run from Output Log:

    py "/home/heinrich/RoboLab/python/benchmark/senior_care/unreal/proj_may/Content/Python/fix_materials.py"
"""

from __future__ import annotations

import unreal


DEFAULT_MAT_PATHS = [
    "/Engine/BasicShapes/BasicShapeMaterial",
    "/Engine/EngineMaterials/DefaultMaterial",
    "/Engine/EngineMaterials/WorldGridMaterial",
]


def _load_default_material():
    for path in DEFAULT_MAT_PATHS:
        try:
            mat = unreal.EditorAssetLibrary.load_asset(path)
            if mat is not None:
                unreal.log(f"[fix_materials] using default material: {path}")
                return mat
        except Exception:
            continue
    raise RuntimeError("No engine default material found; tried " + str(DEFAULT_MAT_PATHS))


def _get_poseable(actor):
    if hasattr(actor, "get_poseable_mesh"):
        try:
            p = actor.get_poseable_mesh()
            if p is not None:
                return p
        except Exception:
            pass
    try:
        comps = list(actor.get_components_by_class(unreal.PoseableMeshComponent))
        return comps[0] if comps else None
    except Exception:
        return None


def _override_all_material_slots(poseable, default_mat) -> int:
    try:
        n = int(poseable.get_num_materials())
    except Exception as exc:
        unreal.log_warning(f"[fix_materials] get_num_materials failed: {exc}")
        return 0
    fixed = 0
    for i in range(n):
        try:
            poseable.set_material(i, default_mat)
            fixed += 1
        except Exception as exc:
            unreal.log_warning(
                f"[fix_materials] set_material({i}) failed: {exc}"
            )
    return fixed


def main() -> None:
    default_mat = _load_default_material()

    ed = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = [
        a for a in ed.get_all_level_actors()
        if a.get_class().get_name() == "MuJoCoSkeletalActor"
    ]
    if not actors:
        unreal.log_warning("[fix_materials] no MuJoCoSkeletalActor in level")
        return

    for actor in actors:
        label = actor.get_actor_label()
        poseable = _get_poseable(actor)
        if poseable is None:
            unreal.log_warning(f"[fix_materials] {label}: no PoseableMesh")
            continue
        n_before = int(poseable.get_num_materials())
        fixed = _override_all_material_slots(poseable, default_mat)
        unreal.log(
            f"[fix_materials] {label}: overrode {fixed}/{n_before} material slot(s)"
        )

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_invalidate_viewports()
    except Exception:
        try:
            unreal.EditorLevelLibrary.editor_invalidate_viewports()
        except Exception:
            pass

    unreal.log(
        "[fix_materials] done. Both meshes should now render as plain grey. "
        "If they're still invisible the problem is geometry/scale, not materials."
    )


main()
