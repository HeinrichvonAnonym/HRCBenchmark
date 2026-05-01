"""Rescale the Franka actor from 1.0 to 100.0.

Reason: ``demo.yaml`` says

    scale: 1 # URDF2FBX 输出以米为单位，UE 以 cm 为单位，需乘 100

The comment correctly identifies the unit mismatch (FBX is in meters, UE is
in cm) but the value contradicts the comment, so the spawned actor was a
1.5 cm tall robot -- effectively a dot at any sensible camera distance.
SMPL-X has ``scale: 100`` (correct) and renders fine.

This script is a non-destructive runtime patch; for a permanent fix also
change the YAML to ``scale: 100`` and re-run ``test_ue.py``.

Run from Output Log:

    py "/home/heinrich/RoboLab/python/benchmark/senior_care/unreal/proj_may/Content/Python/fix_franka_scale.py"
"""

from __future__ import annotations

import unreal


TARGET_SCALE = 100.0


def main() -> None:
    ed = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = list(ed.get_all_level_actors())

    fixed = 0
    for actor in actors:
        if actor.get_class().get_name() != "MuJoCoSkeletalActor":
            continue
        label = actor.get_actor_label()
        if "franka" not in label.lower():
            continue
        before = actor.get_actor_scale3d()
        actor.set_actor_scale3d(unreal.Vector(TARGET_SCALE, TARGET_SCALE, TARGET_SCALE))
        after = actor.get_actor_scale3d()
        unreal.log(
            f"[fix_franka_scale] {label}: scale {before.x} -> {after.x}"
        )
        fixed += 1

    if fixed == 0:
        unreal.log_warning(
            "[fix_franka_scale] no Franka MuJoCoSkeletalActor found"
        )

    try:
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_invalidate_viewports()
    except Exception:
        pass


main()
