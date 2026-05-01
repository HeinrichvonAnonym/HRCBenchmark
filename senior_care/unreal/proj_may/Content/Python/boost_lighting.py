"""Push the scene exposure/lighting so it's visible.

Run from the Output Log:

    py "/home/heinrich/RoboLab/python/benchmark/senior_care/unreal/proj_may/Content/Python/boost_lighting.py"

Why this exists:
    Even though DirectionalLight intensity is 75000 lux and SkyLight is real-
    time-captured, the scene appears nearly black. With
    ``r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange=True`` (set in
    DefaultEngine.ini), manual exposure bias semantics treat the value as a
    log2 luminance target instead of a simple stops offset. Bias=2 maps to a
    very dim target. A sunlit scene needs bias around 10-13.

    On top of that we drop in one fallback PointLight (tagged) to remove
    "is the sun actually working" from the equation.
"""

from __future__ import annotations

import unreal


PPV_TAG = "fix_dark_scene_ppv"
FALLBACK_LIGHT_TAG = "boost_lighting_fallback"

# 7.0 gives a balanced indoor/outdoor look without overexposure.
DESIRED_BIAS_STOPS = 2.0
DIRECTIONAL_INTENSITY_LUX = 75000.0
SKY_INTENSITY = 1.0
FALLBACK_INTENSITY_CD = 50000.0
FALLBACK_RADIUS_CM = 5000.0


def _has_tag(actor, tag: str) -> bool:
    try:
        tags = [str(t) for t in (actor.tags or [])]
    except Exception:
        return False
    return tag in tags


def _patch_post_process(all_actors) -> None:
    target = None
    for a in all_actors:
        if isinstance(a, unreal.PostProcessVolume) and _has_tag(a, PPV_TAG):
            target = a
            break
    if target is None:
        for a in all_actors:
            if isinstance(a, unreal.PostProcessVolume):
                target = a
                break
    if target is None:
        target = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.PostProcessVolume, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
        )
        try:
            target.tags = [unreal.Name(PPV_TAG)]
        except Exception as exc:
            unreal.log_warning(f"[boost_lighting] PPV tag failed: {exc}")
        unreal.log("[boost_lighting] spawned new PostProcessVolume")

    target.set_editor_property("unbound", True)
    target.set_editor_property("priority", 1.0)
    s = target.settings
    s.override_auto_exposure_method = True
    s.auto_exposure_method = unreal.AutoExposureMethod.AEM_MANUAL
    s.override_auto_exposure_bias = True
    s.auto_exposure_bias = DESIRED_BIAS_STOPS
    s.override_auto_exposure_min_brightness = True
    s.auto_exposure_min_brightness = 0.03
    s.override_auto_exposure_max_brightness = True
    s.auto_exposure_max_brightness = 8.0
    target.settings = s
    unreal.log(
        f"[boost_lighting] PostProcessVolume bias -> {DESIRED_BIAS_STOPS} stops"
    )


def _patch_directional(all_actors) -> None:
    for a in all_actors:
        if not isinstance(a, unreal.DirectionalLight):
            continue
        c = a.light_component
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_editor_property("intensity", DIRECTIONAL_INTENSITY_LUX)
        c.set_editor_property("affects_world", True)
        c.set_editor_property("visible", True)
        unreal.log(
            f"[boost_lighting] DirectionalLight intensity -> {DIRECTIONAL_INTENSITY_LUX} lux"
        )


def _patch_skylight(all_actors) -> None:
    for a in all_actors:
        if not isinstance(a, unreal.SkyLight):
            continue
        c = a.light_component
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_editor_property("real_time_capture", True)
        c.set_editor_property("intensity", SKY_INTENSITY)
        try:
            c.recapture_sky()
        except Exception:
            pass
        unreal.log(f"[boost_lighting] SkyLight intensity -> {SKY_INTENSITY}")


def _ensure_fallback_point_light(all_actors) -> None:
    existing = None
    for a in all_actors:
        if isinstance(a, unreal.PointLight) and _has_tag(a, FALLBACK_LIGHT_TAG):
            existing = a
            break

    if existing is None:
        existing = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.PointLight, unreal.Vector(0.0, 0.0, 500.0), unreal.Rotator(0, 0, 0)
        )
        try:
            existing.tags = [unreal.Name(FALLBACK_LIGHT_TAG)]
        except Exception as exc:
            unreal.log_warning(f"[boost_lighting] PointLight tag failed: {exc}")
        unreal.log("[boost_lighting] spawned fallback PointLight at (0,0,500)")
    else:
        unreal.log("[boost_lighting] reusing fallback PointLight")

    c = existing.light_component
    c.set_mobility(unreal.ComponentMobility.MOVABLE)
    c.set_editor_property("intensity", FALLBACK_INTENSITY_CD)
    c.set_editor_property("attenuation_radius", FALLBACK_RADIUS_CM)
    c.set_editor_property("affects_world", True)
    c.set_editor_property("visible", True)


def main() -> None:
    ed = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = list(ed.get_all_level_actors())

    _patch_directional(all_actors)
    _patch_skylight(all_actors)
    _ensure_fallback_point_light(all_actors)
    _patch_post_process(all_actors)

    try:
        unreal.EditorLevelLibrary.editor_invalidate_viewports()
    except Exception:
        pass

    unreal.log("[boost_lighting] done. If still dark, paste the log + a screenshot.")


main()
