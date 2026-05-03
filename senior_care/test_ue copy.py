"""In-editor entry point: load demo.yaml, drive joints from Python, and
stream virtual camera RGBD frames back to the MuJoCo process via ZMQ.

Run this from the Unreal Editor's Output Log (or any editor utility that
exposes the ``py`` command)::

    py "/home/heinrich/roboLab/python/benchmark/senior_care/test_ue.py"

What the script does:
    1. Adds ``python/`` to ``sys.path`` so ``benchmark.senior_care...`` imports.
    2. Calls :func:`load_scene_for_editor` to import every FBX listed in
       ``config/demo.yaml`` as a SkeletalMesh, generate a per-skeleton
       runtime ControlRig, spawn a SkeletalMeshActor in the active level,
       and apply the initial joint state from the YAML.
    3. Spawns ``CineCameraActor`` instances for every entry under
       ``cameras:`` in the YAML, each equipped with two
       ``SceneCaptureComponent2D`` components (RGB + depth).
    4. Opens a ZMQ PUB socket on port 5557 and registers a Slate pre-tick
       callback that, on every editor tick:
         * rotates the Franka's ``panda_joint1`` (a sweep from -1 to +1 rad)
         * rolls the SMPL-X human's right forearm
           (``r_elbow`` token = bone ``right_elbow``, local Z = forearm axis).
         * captures RGB + depth from each virtual camera and publishes
           ``CameraFrame`` messages over ZMQ to the MuJoCo subscriber.

The script is idempotent -- running it multiple times reuses imported uassets
and re-spawns fresh actors (the previous actors stay in the level; remove
them manually if you want a clean slate).
"""

from __future__ import annotations

import math
import struct
import sys
import time
from array import array as _arr
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
from benchmark.senior_care.ue_mujoco_bridge.camera_signal import CameraFrame  # noqa: E402
from benchmark.senior_care.ue_mujoco_bridge.ue_zmq_session import UeZmqSession  # noqa: E402


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

# ZMQ camera publisher address. The MuJoCo subscriber connects to this.
# Change to e.g. "tcp://*:5558" if port 5557 is taken.
ZMQ_CAMERA_ADDRESS = "tcp://*:5557"

# RGBD capture rate. UE editor ticks at ~60 Hz; capturing every tick stalls
# the editor on the CPU readback (read_render_target* is a blocking
# RHI->system-memory copy). 0.5 Hz = one frame every 2 s gives a usable
# preview without dragging the editor framerate down.
CAMERA_CAPTURE_HZ = 0.5
CAMERA_CAPTURE_PERIOD_S = 1.0 / CAMERA_CAPTURE_HZ

# Set to False to skip camera capture + ZMQ streaming even when cameras are
# configured in the YAML (useful when iterating on rendering without needing
# the MuJoCo side running).
STREAM_CAMERAS = True


# ---------------------------------------------------------------------------
# Pixel-data helpers (numpy-free — works in UE's embedded Python)
# ---------------------------------------------------------------------------


def _read_rgb_bytes(
    world: unreal.World,
    rt: unreal.TextureRenderTarget2D,
    cap: unreal.SceneCaptureComponent2D,
    width: int,
    height: int,
) -> bytes:
    """Trigger a capture and read back raw RGB bytes from a render target.

    Returns H×W×3 uint8 bytes (R, G, B order, row-major).

    UE 5.x ``RenderingLibrary.read_render_target`` returns the pixel array
    directly (not via an out-parameter); passing a pre-allocated Array as the
    third positional triggers TypeError "Cannot nativize 'Array' as 'bool'"
    because that slot is the ``normalize`` flag.
    """
    cap.capture_scene()
    pixel_data = unreal.RenderingLibrary.read_render_target(world, rt)
    if pixel_data is None:
        unreal.log_warning(
            "[test_ue] RGB read_render_target returned None; sending zeros"
        )
        return bytes(width * height * 3)
    n = len(pixel_data)
    if n != width * height:
        unreal.log_warning(
            f"[test_ue] RGB pixel_data length {n} != {width * height}; "
            "returning zeros"
        )
        return bytes(width * height * 3)
    return bytes(_arr("B", (ch for p in pixel_data for ch in (p.r, p.g, p.b))))


def _read_depth_bytes(
    world: unreal.World,
    rt: unreal.TextureRenderTarget2D,
    cap: unreal.SceneCaptureComponent2D,
    width: int,
    height: int,
) -> bytes:
    """Trigger a depth capture and read back raw float32 bytes (metres).

    UE's ``SCS_SCENE_DEPTH`` source stores depth in UE units (cm); we
    divide by 100 to convert to metres before packing.

    ``read_render_target_raw`` returns ``Array[LinearColor]`` directly; the
    third positional is ``normalize`` (bool). We pass ``False`` so the R
    channel keeps the raw linear scene-depth value rather than being rescaled
    to ``[0, 1]``.
    """
    cap.capture_scene()
    depth_data = unreal.RenderingLibrary.read_render_target_raw(world, rt, False)
    if depth_data is None:
        unreal.log_warning(
            "[test_ue] depth read_render_target_raw returned None; sending zeros"
        )
        return struct.pack(f"<{width * height}f", *([0.0] * (width * height)))
    n = len(depth_data)
    if n != width * height:
        unreal.log_warning(
            f"[test_ue] depth_data length {n} != {width * height}; "
            "returning zeros"
        )
        return struct.pack(f"<{width * height}f", *([0.0] * (width * height)))
    # R channel holds linear depth in UE units (cm) → convert to metres.
    depth_m = [p.r / 100.0 for p in depth_data]
    return struct.pack(f"<{n}f", *depth_m)


# ---------------------------------------------------------------------------
# Tick callback builder
# ---------------------------------------------------------------------------


def _build_tick_callback(
    driver,
    cameras: list[dict],
    zmq_session: UeZmqSession | None,
) -> object:
    """Return an editor-tick callback that animates joints and streams cameras.

    Parameters
    ----------
    driver      : :class:`UeJointDriver` (no-op shim, kept for API compat).
    cameras     : List of camera dicts from :func:`load_scene_for_editor`.
    zmq_session : Open :class:`UeZmqSession` with camera PUB socket, or
        ``None`` when camera streaming is disabled.
    """
    elapsed = {"t": 0.0}
    # Initialise the "last capture" timestamp far enough in the past that
    # the very first tick triggers a capture (rather than waiting 2 s for
    # the first frame).
    last_capture = {"t": -CAMERA_CAPTURE_PERIOD_S}
    cam_seqs: dict[str, int] = {cam["spec"].name: 0 for cam in cameras}

    def _on_tick(delta_seconds: float) -> None:
        elapsed["t"] += float(delta_seconds)
        t = elapsed["t"]

        # ---- Joint animation (unchanged from original test_ue.py) ----------
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

        # ---- Camera capture + ZMQ streaming --------------------------------
        if not cameras or zmq_session is None:
            return

        # Throttle to CAMERA_CAPTURE_HZ. Without this the readback runs
        # every editor tick (~60 Hz) which makes the editor crawl.
        if (t - last_capture["t"]) < CAMERA_CAPTURE_PERIOD_S:
            return
        last_capture["t"] = t

        try:
            world = unreal.EditorLevelLibrary.get_editor_world()
        except Exception as exc:
            unreal.log_warning(f"[test_ue] get_editor_world failed: {exc}")
            return

        for cam_info in cameras:
            spec = cam_info["spec"]
            try:
                rgb_bytes = _read_rgb_bytes(
                    world,
                    cam_info["rt_rgb"],
                    cam_info["cap_rgb"],
                    spec.width,
                    spec.height,
                )
                depth_bytes = _read_depth_bytes(
                    world,
                    cam_info["rt_depth"],
                    cam_info["cap_depth"],
                    spec.width,
                    spec.height,
                )
            except Exception as exc:
                unreal.log_warning(
                    f"[test_ue] camera '{spec.name}' capture failed: {exc}"
                )
                continue

            cam_seqs[spec.name] += 1
            frame = CameraFrame(
                camera_name=spec.name,
                seq=cam_seqs[spec.name],
                timestamp=t,
                width=spec.width,
                height=spec.height,
                fov=spec.fov,
                position=list(spec.position_m),
                orientation=list(spec.orientation_wxyz),
                rgb_bytes=rgb_bytes,
                depth_bytes=depth_bytes,
            )
            try:
                zmq_session.send_camera_frame(frame)
            except Exception as exc:
                unreal.log_warning(
                    f"[test_ue] ZMQ send for camera '{spec.name}' failed: {exc}"
                )

    return _on_tick


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def main() -> None:
    if not CONFIG_PATH.exists():
        unreal.log_error(f"[test_ue] config not found: {CONFIG_PATH}")
        return

    unreal.log(
        f"[test_ue] loading scene from {CONFIG_PATH} "
        f"(apply_initial_state={APPLY_INITIAL_STATE}, "
        f"drive_test_joints={DRIVE_TEST_JOINTS}, "
        f"stream_cameras={STREAM_CAMERAS})"
    )
    _scene, _loader, driver, cameras = load_scene_for_editor(
        CONFIG_PATH, apply_initial_state=APPLY_INITIAL_STATE
    )

    # ---- Tear down previous tick callback FIRST --------------------------
    # (Important: must happen BEFORE opening a new ZMQ PUB on the same port,
    # otherwise the new bind() fails with "Address already in use" because
    # the previous session still holds 5557.)
    previous_handle = getattr(unreal, "_senior_care_tick_handle", None)
    if previous_handle is not None:
        try:
            unreal.unregister_slate_pre_tick_callback(previous_handle)
        except Exception:
            pass
        unreal._senior_care_tick_handle = None  # type: ignore[attr-defined]

    # ---- Close previous ZMQ session (if any) ----------------------------
    # ``UeZmqSession.open_camera_pub`` sets ZMQ LINGER=0 so this close()
    # releases the port immediately (no TIME_WAIT).
    previous_zmq = getattr(unreal, "_senior_care_zmq_session", None)
    if previous_zmq is not None:
        try:
            previous_zmq.close()
        except Exception:
            pass
        unreal._senior_care_zmq_session = None  # type: ignore[attr-defined]

    # ---- ZMQ camera publisher (now safe to open) ------------------------
    zmq_session: UeZmqSession | None = None
    if cameras and STREAM_CAMERAS:
        zmq_session = UeZmqSession()  # SUB socket (unused here, but fine)
        try:
            zmq_session.open_camera_pub(ZMQ_CAMERA_ADDRESS)
            unreal.log(
                f"[test_ue] camera ZMQ PUB opened on {ZMQ_CAMERA_ADDRESS} "
                f"({len(cameras)} camera(s): "
                + ", ".join(c["spec"].name for c in cameras)
                + ")"
            )
        except Exception as exc:
            unreal.log_error(f"[test_ue] could not open camera ZMQ PUB: {exc}")
            zmq_session = None
    elif cameras and not STREAM_CAMERAS:
        unreal.log(
            f"[test_ue] {len(cameras)} camera(s) spawned but STREAM_CAMERAS=False; "
            "ZMQ not opened."
        )

    if not DRIVE_TEST_JOINTS and not (cameras and STREAM_CAMERAS):
        unreal.log(
            "[test_ue] DRIVE_TEST_JOINTS=False and no active camera streaming; "
            "not registering tick callback."
        )
        return

    callback = _build_tick_callback(driver, cameras, zmq_session)
    handle = unreal.register_slate_pre_tick_callback(callback)
    unreal._senior_care_tick_handle = handle  # type: ignore[attr-defined]
    unreal._senior_care_zmq_session = zmq_session  # type: ignore[attr-defined]

    unreal.log(
        "[test_ue] tick callback registered. "
        + (
            f"panda_joint1 will sweep +/- "
            f"{PANDA_JOINT1_AMPLITUDE_RAD:.2f} rad every {PANDA_JOINT1_PERIOD_S:.1f}s; "
            f"right forearm rolls +/- "
            f"{HUMAN_FOREARM_AMPLITUDE_RAD:.2f} rad every {HUMAN_FOREARM_PERIOD_S:.1f}s. "
            if DRIVE_TEST_JOINTS
            else ""
        )
        + (
            f"Camera streaming: {len(cameras)} camera(s) → {ZMQ_CAMERA_ADDRESS}."
            if cameras and STREAM_CAMERAS and zmq_session is not None
            else ""
        )
    )


main()
