"""One-shot helper: create /Game/DemoMap with a fully-dynamic lit environment.

Run via UE editor commandlet:

    UnrealEditor-Cmd proj_may.uproject \
        -run=pythonscript \
        -script="Content/Python/init_demo_map.py" \
        -unattended -nullrhi -nosplash

Why everything is Movable: the demo never bakes lightmaps. Static or Stationary
lights would surface the "Lighting needs to be rebuilt" warning AND would emit
zero light until baked, leaving the viewport black. Movable lights work
immediately at editor tick speed, which is what we need for streaming
MuJoCo->UE skeletal frames.

Note on intensity units: ``UDirectionalLightComponent`` in UE 5.6 does NOT
expose an ``intensity_units`` property (only ``ULocalLightComponent`` does).
Directional light intensity is always interpreted as Lux, so writing
``intensity = 75000`` directly gives a sun-like value -- no unit override
needed.

Why a PostProcessVolume with manual exposure: SM5-only / no-Lumen pipelines
(see ``Config/DefaultEngine.ini``) have weak indirect lighting and the auto
eye-adaptation can sit at the dim end. A small +2 EV bias guarantees that the
viewport is visibly lit on first open without us having to babysit lighting.

Set ``FORCE_REBUILD = False`` to make the script a no-op when the asset already
exists.
"""

from __future__ import annotations

import unreal


MAP_PACKAGE = "/Game/DemoMap"
FORCE_REBUILD = True

SUN_INTENSITY_LUX = 75000.0
SKY_INTENSITY = 1.0
# r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange=True (DefaultEngine.ini)
# changes the bias from a simple EV-stops offset into a log2 luminance target.
# 7.0 gives a balanced indoor/outdoor look without overexposure.
EXPOSURE_BIAS_STOPS = 0.5


def _safe_set(obj, prop_name: str, value) -> None:
    try:
        obj.set_editor_property(prop_name, value)
    except Exception as exc:  # noqa: BLE001
        unreal.log_warning(
            f"[init_demo_map] could not set '{prop_name}' on {obj}: {exc}"
        )


def _force_movable(scene_component) -> None:
    if scene_component is None:
        return
    try:
        scene_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    except Exception as exc:  # noqa: BLE001
        unreal.log_warning(
            f"[init_demo_map] set_mobility(MOVABLE) failed on {scene_component}: {exc}"
        )


def _ensure_demo_map() -> None:
    editor_asset = unreal.EditorAssetLibrary
    level_lib = unreal.EditorLevelLibrary

    if editor_asset.does_asset_exist(MAP_PACKAGE):
        if not FORCE_REBUILD:
            unreal.log(
                f"[init_demo_map] {MAP_PACKAGE} already exists and FORCE_REBUILD=False; nothing to do."
            )
            return
        unreal.log(f"[init_demo_map] FORCE_REBUILD=True -> deleting old {MAP_PACKAGE}")
        editor_asset.delete_asset(MAP_PACKAGE)

    unreal.log(f"[init_demo_map] creating new empty level at {MAP_PACKAGE}")
    level_lib.new_level(MAP_PACKAGE)

    unreal.log("[init_demo_map] populating sky / sun / fog / floor / player_start (all Movable)")

    level_lib.spawn_actor_from_class(
        unreal.SkyAtmosphere, unreal.Vector(0, 0, 0)
    )

    sky_light = level_lib.spawn_actor_from_class(
        unreal.SkyLight, unreal.Vector(0, 0, 200)
    )
    sky_component = sky_light.light_component
    _force_movable(sky_component)
    if sky_component is not None:
        _safe_set(sky_component, "real_time_capture", True)
        _safe_set(sky_component, "intensity", SKY_INTENSITY)
        try:
            sky_component.recapture_sky()
        except Exception as exc:  # noqa: BLE001
            unreal.log_warning(f"[init_demo_map] recapture_sky() failed: {exc}")

    level_lib.spawn_actor_from_class(
        unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0)
    )

    sun = level_lib.spawn_actor_from_class(
        unreal.DirectionalLight,
        unreal.Vector(0, 0, 500),
        unreal.Rotator(-45.0, 30.0, 0.0),
    )
    sun_component = sun.light_component
    _force_movable(sun_component)
    if sun_component is not None:
        _safe_set(sun_component, "intensity", SUN_INTENSITY_LUX)
        _safe_set(sun_component, "atmosphere_sun_light", True)

    level_lib.spawn_actor_from_class(
        unreal.PlayerStart,
        unreal.Vector(0, 0, 200),
        unreal.Rotator(0.0, 0.0, 0.0),
    )

    floor = level_lib.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0, 0, -50)
    )
    _force_movable(floor.static_mesh_component)
    cube_mesh = editor_asset.load_asset("/Engine/BasicShapes/Cube")
    if cube_mesh is None:
        unreal.log_warning(
            "[init_demo_map] failed to load /Engine/BasicShapes/Cube; floor will be invisible"
        )
    else:
        floor.static_mesh_component.set_static_mesh(cube_mesh)
        floor.set_actor_scale3d(unreal.Vector(20.0, 20.0, 0.1))

    ppv = level_lib.spawn_actor_from_class(
        unreal.PostProcessVolume, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0)
    )
    _safe_set(ppv, "unbound", True)
    _safe_set(ppv, "priority", 1.0)
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

    level_lib.save_current_level()
    unreal.log(f"[init_demo_map] saved {MAP_PACKAGE}")


_ensure_demo_map()
