"""Live patch for "DemoMap is too dark" without restarting the editor.

Run from the Output Log:

    py "/home/heinrich/RoboLab/python/benchmark/senior_care/unreal/proj_may/Content/Python/fix_dark_scene.py"

Notes on property names (UE 5.6):
    * UDirectionalLightComponent does NOT expose ``intensity_units``: the
      directional light's intensity is always interpreted as Lux, so just
      writing ``intensity = 75000`` is enough.
    * ULocalLightComponent (Point/Spot/Rect) DOES have ``intensity_units``,
      but we don't have those in this scene.

Idempotent: re-running it tweaks the existing PostProcessVolume rather than
adding a second one.
"""

from __future__ import annotations

import unreal


PPV_TAG = "fix_dark_scene_ppv"
SUN_INTENSITY_LUX = 75000.0
SKY_INTENSITY = 1.0
# r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange=True (DefaultEngine.ini)
# changes the bias from a simple EV-stops offset into a log2 luminance target.
# 7.0 gives a balanced indoor/outdoor look without overexposure.
EXPOSURE_BIAS_STOPS = 2.0


def _log(msg: str) -> None:
    unreal.log(f"[fix_dark_scene] {msg}")


def _try_get(obj, prop_name: str):
    try:
        return obj.get_editor_property(prop_name)
    except Exception as exc:  # noqa: BLE001
        return f"<no '{prop_name}': {exc}>"


def _try_set(obj, prop_name: str, value) -> bool:
    try:
        obj.set_editor_property(prop_name, value)
        return True
    except Exception as exc:  # noqa: BLE001
        _log(f"  set '{prop_name}' on {obj} failed: {exc}")
        return False


def _patch_directional_light(actor: unreal.DirectionalLight) -> None:
    c = actor.light_component
    before = {
        "mobility": _try_get(c, "mobility"),
        "intensity": _try_get(c, "intensity"),
        "atmosphere_sun_light": _try_get(c, "atmosphere_sun_light"),
        "affects_world": _try_get(c, "affects_world"),
        "visible": _try_get(c, "visible"),
    }
    _log(f"DirectionalLight BEFORE: {before}")

    try:
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
    except Exception as exc:  # noqa: BLE001
        _log(f"  set_mobility failed: {exc}")

    _try_set(c, "intensity", SUN_INTENSITY_LUX)
    _try_set(c, "atmosphere_sun_light", True)
    _try_set(c, "affects_world", True)
    _try_set(c, "visible", True)

    after = {
        "mobility": _try_get(c, "mobility"),
        "intensity": _try_get(c, "intensity"),
        "atmosphere_sun_light": _try_get(c, "atmosphere_sun_light"),
        "affects_world": _try_get(c, "affects_world"),
        "visible": _try_get(c, "visible"),
    }
    _log(f"DirectionalLight AFTER:  {after}")


def _patch_sky_light(actor: unreal.SkyLight) -> None:
    c = actor.light_component
    before = {
        "mobility": _try_get(c, "mobility"),
        "intensity": _try_get(c, "intensity"),
        "real_time_capture": _try_get(c, "real_time_capture"),
        "source_type": _try_get(c, "source_type"),
    }
    _log(f"SkyLight BEFORE: {before}")

    try:
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
    except Exception as exc:  # noqa: BLE001
        _log(f"  set_mobility failed: {exc}")

    _try_set(c, "real_time_capture", True)
    _try_set(c, "intensity", SKY_INTENSITY)

    try:
        c.recapture_sky()
    except Exception as exc:  # noqa: BLE001
        _log(f"  recapture_sky failed: {exc}")

    after = {
        "mobility": _try_get(c, "mobility"),
        "intensity": _try_get(c, "intensity"),
        "real_time_capture": _try_get(c, "real_time_capture"),
    }
    _log(f"SkyLight AFTER:  {after}")


def _ensure_post_process(level_actors: list) -> None:
    existing = []
    for a in level_actors:
        if not isinstance(a, unreal.PostProcessVolume):
            continue
        try:
            tags = [str(t) for t in (a.tags or [])]
        except Exception:  # noqa: BLE001
            tags = []
        if PPV_TAG in tags:
            existing.append(a)

    if existing:
        ppv = existing[0]
        _log(f"reusing existing PostProcessVolume {ppv}")
    else:
        ppv = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.PostProcessVolume, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
        )
        try:
            ppv.tags = [unreal.Name(PPV_TAG)]
        except Exception as exc:  # noqa: BLE001
            _log(f"  could not tag PPV: {exc}")
        _log(f"spawned new PostProcessVolume {ppv}")

    _try_set(ppv, "unbound", True)
    _try_set(ppv, "priority", 1.0)

    settings = ppv.settings
    settings.override_auto_exposure_method = True
    settings.auto_exposure_method = unreal.AutoExposureMethod.AEM_MANUAL
    settings.override_auto_exposure_bias = True
    settings.auto_exposure_bias = EXPOSURE_BIAS_STOPS
    settings.override_auto_exposure_min_brightness = True
    settings.auto_exposure_min_brightness = 0.03
    settings.override_auto_exposure_max_brightness = True
    settings.auto_exposure_max_brightness = 8.0
    ppv.settings = settings
    _log(
        f"PostProcessVolume: unbound=True method=Manual bias={EXPOSURE_BIAS_STOPS} stops"
    )


def main() -> None:
    ed = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = list(ed.get_all_level_actors())

    dir_lights = [a for a in all_actors if isinstance(a, unreal.DirectionalLight)]
    sky_lights = [a for a in all_actors if isinstance(a, unreal.SkyLight)]

    _log(
        f"world has {len(all_actors)} actors total; "
        f"{len(dir_lights)} DirectionalLight, {len(sky_lights)} SkyLight"
    )

    if not dir_lights:
        _log("WARNING: no DirectionalLight in the world; spawning one")
        sun = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.DirectionalLight,
            unreal.Vector(0, 0, 500),
            unreal.Rotator(-45.0, 30.0, 0.0),
        )
        dir_lights = [sun]
    for sun in dir_lights:
        _patch_directional_light(sun)

    if not sky_lights:
        _log("WARNING: no SkyLight in the world; spawning one")
        sky = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.SkyLight, unreal.Vector(0, 0, 200)
        )
        sky_lights = [sky]
    for sky in sky_lights:
        _patch_sky_light(sky)

    _ensure_post_process(all_actors)

    _log("done. If still black, paste the BEFORE/AFTER lines back to me.")


main()
