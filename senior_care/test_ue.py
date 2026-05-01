"""In-editor entry point: load demo.yaml and drive joints from Python.

Run this from the Unreal Editor's Output Log (or any editor utility that
exposes the ``py`` command)::

    py "/home/heinrich/roboLab/python/benchmark/senior_care/test_ue.py"

What the script does:
    1. Adds ``python/`` to ``sys.path`` so ``benchmark.senior_care...`` imports.
    2. Calls :func:`load_scene_for_editor` to import every FBX listed in
       ``config/demo.yaml`` as a SkeletalMesh, generate a per-skeleton
       runtime ControlRig, spawn a SkeletalMeshActor in the active level,
       and apply the initial joint state from the YAML.
    3. Registers a Slate pre-tick callback that, on every editor tick:
         * rotates the Franka's ``panda_joint1`` (a sweep from -1 to +1 rad)
         * rolls the SMPL-X human's right forearm
           (``r_elbow`` token = bone ``right_elbow``, local Z = forearm axis).

The script is idempotent -- running it multiple times reuses imported uassets
and re-spawns fresh actors (the previous actors stay in the level; remove
them manually if you want a clean slate).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path


_THIS_DIR = Path(__file__).resolve().parent           # .../senior_care/
_PYTHON_ROOT = _THIS_DIR.parents[1]                   # .../python/

if str(_PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(_PYTHON_ROOT))


import importlib  # noqa: E402

import unreal  # noqa: E402  -- editor module, only available inside UE

# Force-reload the senior_care modules so iteration on ue_script.py /
# scene/ue_scene.py during a long-running editor session picks up edits
# without restarting UE.
for _mod_name in list(sys.modules):
    if _mod_name.startswith("benchmark.senior_care"):
        try:
            importlib.reload(sys.modules[_mod_name])
        except Exception as _exc:  # noqa: BLE001
            unreal.log_warning(f"[test_ue] reload of {_mod_name} failed: {_exc}")

from benchmark.senior_care.base.ue_script import load_scene_for_editor  # noqa: E402


CONFIG_PATH = _THIS_DIR / "config" / "demo.yaml"

# When debugging "I don't see the meshes at all", flip this to False to keep
# the meshes in their FBX bind pose (no initial-state rotations applied).
# That isolates render-setup problems from "the initial pose puts the mesh
# out of view" problems.
APPLY_INITIAL_STATE = True

# When debugging rendering, also flip this to False so the per-tick callback
# stops poking the rig (so a black viewport stays black until you decide it's
# really a render problem and not the animation overwriting things).
DRIVE_TEST_JOINTS = False

# Drive amplitudes / speeds for the two test motions.
PANDA_JOINT1_AMPLITUDE_RAD = 1.0
PANDA_JOINT1_PERIOD_S = 4.0
HUMAN_FOREARM_AMPLITUDE_RAD = 0.8
HUMAN_FOREARM_PERIOD_S = 3.0


def _build_tick_callback(driver):
    """Return an editor-tick callback that animates the two test joints."""
    elapsed = {"t": 0.0}

    def _on_tick(delta_seconds: float) -> None:
        elapsed["t"] += float(delta_seconds)
        t = elapsed["t"]

        panda_phase = (2.0 * math.pi / PANDA_JOINT1_PERIOD_S) * t
        panda_joint1 = PANDA_JOINT1_AMPLITUDE_RAD * math.sin(panda_phase)
        try:
            driver.set_joint_angle(
                "franka_emika_panda",
                "panda_joint1",
                panda_joint1,
                axis="z",
            )
        except KeyError:
            pass

        forearm_phase = (2.0 * math.pi / HUMAN_FOREARM_PERIOD_S) * t
        forearm = HUMAN_FOREARM_AMPLITUDE_RAD * math.sin(forearm_phase)
        try:
            driver.set_joint_angle(
                "simpl_neutral",
                "r_elbow",
                forearm,
                axis="z",
            )
        except KeyError:
            pass

    return _on_tick


def main() -> None:
    if not CONFIG_PATH.exists():
        unreal.log_error(f"[test_ue] config not found: {CONFIG_PATH}")
        return

    unreal.log(
        f"[test_ue] loading scene from {CONFIG_PATH} "
        f"(apply_initial_state={APPLY_INITIAL_STATE}, "
        f"drive_test_joints={DRIVE_TEST_JOINTS})"
    )
    _scene, _loader, driver = load_scene_for_editor(
        CONFIG_PATH, apply_initial_state=APPLY_INITIAL_STATE
    )

    # Always tear down the previous tick callback (even if we are not
    # registering a new one), otherwise an old run keeps animating.
    previous_handle = getattr(unreal, "_senior_care_tick_handle", None)
    if previous_handle is not None:
        try:
            unreal.unregister_slate_pre_tick_callback(previous_handle)
        except Exception:
            pass
        unreal._senior_care_tick_handle = None  # type: ignore[attr-defined]

    if not DRIVE_TEST_JOINTS:
        unreal.log(
            "[test_ue] DRIVE_TEST_JOINTS=False; not registering tick callback."
        )
        return

    callback = _build_tick_callback(driver)
    handle = unreal.register_slate_pre_tick_callback(callback)
    unreal._senior_care_tick_handle = handle  # type: ignore[attr-defined]

    unreal.log(
        "[test_ue] tick callback registered. "
        "panda_joint1 will sweep +/- "
        f"{PANDA_JOINT1_AMPLITUDE_RAD:.2f} rad every {PANDA_JOINT1_PERIOD_S:.1f}s; "
        "right forearm rolls +/- "
        f"{HUMAN_FOREARM_AMPLITUDE_RAD:.2f} rad every {HUMAN_FOREARM_PERIOD_S:.1f}s."
    )


main()
