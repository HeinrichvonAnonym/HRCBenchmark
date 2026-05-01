"""Diagnose 'still black' even though all lights look correct.

Run from the Output Log:

    py "/home/heinrich/RoboLab/python/benchmark/senior_care/unreal/proj_may/Content/Python/focus_viewport.py"

What it does:
    1. Lists every actor in the level so we can verify SkyAtmosphere /
       ExponentialHeightFog / floor are actually there.
    2. Reads + prints the current perspective viewport camera transform.
    3. Snaps the viewport camera to a known-good vantage:
       Location (-800, -800, 400) looking toward the origin where the floor /
       PlayerStart / SkyLight live.
    4. Recaptures the SkyLight (real-time capture sometimes needs a kick after
       SkyAtmosphere parameters change).
    5. Issues a few console commands to make absolutely sure lighting is on
       and the viewport is in real-time mode.
"""

from __future__ import annotations

import unreal


def _exec_cmd(world, cmd: str) -> None:
    unreal.log(f"[focus_viewport] cmd: {cmd}")
    unreal.SystemLibrary.execute_console_command(world, cmd)


def _list_actors(world) -> None:
    ed = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = list(ed.get_all_level_actors())
    unreal.log(f"[focus_viewport] {len(actors)} actor(s) in {world.get_name()}:")
    for a in actors:
        cls = a.get_class().get_name()
        loc = a.get_actor_location()
        unreal.log(
            f"    - {cls:<28} {a.get_actor_label():<32} "
            f"@ ({loc.x:.0f}, {loc.y:.0f}, {loc.z:.0f})"
        )


def _move_camera() -> None:
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    try:
        loc, rot = ues.get_level_viewport_camera_info()
        unreal.log(
            f"[focus_viewport] camera BEFORE: "
            f"loc=({loc.x:.0f},{loc.y:.0f},{loc.z:.0f}) "
            f"rot=(p={rot.pitch:.0f},y={rot.yaw:.0f},r={rot.roll:.0f})"
        )
    except Exception as exc:  # noqa: BLE001
        unreal.log_warning(f"[focus_viewport] could not read camera: {exc}")

    target_loc = unreal.Vector(-300.0, -300.0, 200.0)
    target_rot = unreal.Rotator(roll=0.0, pitch=-25.0, yaw=45.0)
    try:
        ues.set_level_viewport_camera_info(target_loc, target_rot)
        unreal.log(
            f"[focus_viewport] camera AFTER:  "
            f"loc=({target_loc.x:.0f},{target_loc.y:.0f},{target_loc.z:.0f}) "
            f"rot=(p={target_rot.pitch:.0f},y={target_rot.yaw:.0f},r={target_rot.roll:.0f})"
        )
    except Exception as exc:  # noqa: BLE001
        unreal.log_warning(f"[focus_viewport] could not set camera: {exc}")

    try:
        unreal.EditorLevelLibrary.editor_invalidate_viewports()
        unreal.log("[focus_viewport] forced viewport redraw")
    except Exception as exc:  # noqa: BLE001
        unreal.log_warning(f"[focus_viewport] invalidate_viewports failed: {exc}")


def _recapture_sky() -> None:
    ed = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for a in ed.get_all_level_actors():
        if isinstance(a, unreal.SkyLight):
            try:
                a.light_component.recapture_sky()
                unreal.log("[focus_viewport] SkyLight.recapture_sky() OK")
            except Exception as exc:  # noqa: BLE001
                unreal.log_warning(f"[focus_viewport] recapture_sky failed: {exc}")


def main() -> None:
    world = unreal.EditorLevelLibrary.get_editor_world()
    _list_actors(world)
    _move_camera()
    _recapture_sky()

    _exec_cmd(world, "ShowFlag.Lighting 1")
    _exec_cmd(world, "ShowFlag.Atmosphere 1")
    _exec_cmd(world, "ShowFlag.Fog 1")
    _exec_cmd(world, "ShowFlag.SkyLighting 1")
    _exec_cmd(world, "r.SkyAtmosphere 1")
    _exec_cmd(world, "stat fps")

    unreal.log(
        "[focus_viewport] done. If the viewport is STILL black, click inside "
        "the perspective viewport and press Ctrl+R to enable Realtime."
    )


main()
