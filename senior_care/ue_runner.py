"""UE editor-side demo: load YAML scene, optional test joint motion, stream cameras over ZMQ."""

from __future__ import annotations

import importlib
import math
import signal
import struct
import sys
from array import array as _arr
from pathlib import Path
from types import FrameType
from typing import Any, Callable

import unreal  # type: ignore[import-not-found]

from benchmark.senior_care.base.ue_script import load_scene_for_editor
from benchmark.senior_care.ue_mujoco_bridge.camera_signal import CameraFrame
from benchmark.senior_care.ue_mujoco_bridge.ue_zmq_session import UeZmqSession


def _read_rgb_bytes(
    world: unreal.World,
    rt: unreal.TextureRenderTarget2D,
    cap: unreal.SceneCaptureComponent2D,
    width: int,
    height: int,
) -> bytes:
    cap.capture_scene()
    pixel_data = unreal.RenderingLibrary.read_render_target(world, rt)
    if pixel_data is None:
        unreal.log_warning(
            "[UeEditorRunner] RGB read_render_target returned None; sending zeros"
        )
        return bytes(width * height * 3)
    n = len(pixel_data)
    if n != width * height:
        unreal.log_warning(
            f"[UeEditorRunner] RGB pixel_data length {n} != {width * height}; "
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
    cap.capture_scene()
    depth_data = unreal.RenderingLibrary.read_render_target_raw(world, rt, False)
    if depth_data is None:
        unreal.log_warning(
            "[UeEditorRunner] depth read_render_target_raw returned None; sending zeros"
        )
        return struct.pack(f"<{width * height}f", *([0.0] * (width * height)))
    n = len(depth_data)
    if n != width * height:
        unreal.log_warning(
            f"[UeEditorRunner] depth_data length {n} != {width * height}; "
            "returning zeros"
        )
        return struct.pack(f"<{width * height}f", *([0.0] * (width * height)))
    depth_m = [p.r / 100.0 for p in depth_data]
    return struct.pack(f"<{n}f", *depth_m)


def _build_tick_callback(
    driver: Any,
    cameras: list[dict],
    zmq_session: UeZmqSession | None,
    *,
    drive_test_joints: bool,
    panda_amplitude_rad: float,
    panda_period_s: float,
    human_forearm_amplitude_rad: float,
    human_forearm_period_s: float,
    camera_capture_period_s: float,
) -> Callable[[float], None]:
    elapsed = {"t": 0.0}
    last_capture = {"t": -camera_capture_period_s}
    cam_seqs: dict[str, int] = {cam["spec"].name: 0 for cam in cameras}

    def _on_tick(delta_seconds: float) -> None:
        elapsed["t"] += float(delta_seconds)
        t = elapsed["t"]

        if drive_test_joints:
            panda_phase = (2.0 * math.pi / panda_period_s) * t
            panda_joint1 = panda_amplitude_rad * math.sin(panda_phase)
            try:
                driver.set_joint_angle(
                    "franka_emika_panda",
                    "panda_joint1",
                    panda_joint1,
                    axis="z",
                )
            except KeyError:
                pass

            forearm_phase = (2.0 * math.pi / human_forearm_period_s) * t
            forearm = human_forearm_amplitude_rad * math.sin(forearm_phase)
            try:
                driver.set_joint_angle(
                    "simpl_neutral",
                    "r_elbow",
                    forearm,
                    axis="z",
                )
            except KeyError:
                pass

        if not cameras or zmq_session is None:
            return

        if (t - last_capture["t"]) < camera_capture_period_s:
            return
        last_capture["t"] = t

        try:
            world = unreal.EditorLevelLibrary.get_editor_world()
        except Exception as exc:
            unreal.log_warning(f"[UeEditorRunner] get_editor_world failed: {exc}")
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
                    f"[UeEditorRunner] camera '{spec.name}' capture failed: {exc}"
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
                    f"[UeEditorRunner] ZMQ send for camera '{spec.name}' failed: {exc}"
                )

    return _on_tick


class UeEditorRunner:
    """Registers Slate pre-tick; ``stop()`` tears down callback and camera ZMQ."""

    def __init__(
        self,
        *,
        config_path: Path,
        apply_initial_state: bool = True,
        drive_test_joints: bool = False,
        stream_cameras: bool = True,
        zmq_camera_address: str = "tcp://*:5557",
        camera_capture_hz: float = 0.1,
        reload_senior_care_modules: bool = True,
        python_parent: Path | None = None,
        panda_joint1_amplitude_rad: float = 1.0,
        panda_joint1_period_s: float = 4.0,
        human_forearm_amplitude_rad: float = 0.8,
        human_forearm_period_s: float = 3.0,
    ) -> None:
        self.config_path = config_path
        self.apply_initial_state = apply_initial_state
        self.drive_test_joints = drive_test_joints
        self.stream_cameras = stream_cameras
        self.zmq_camera_address = zmq_camera_address
        self.camera_capture_period_s = 1.0 / camera_capture_hz if camera_capture_hz > 0 else 0.0
        self.reload_senior_care_modules = reload_senior_care_modules
        self.python_parent = python_parent
        self.panda_joint1_amplitude_rad = panda_joint1_amplitude_rad
        self.panda_joint1_period_s = panda_joint1_period_s
        self.human_forearm_amplitude_rad = human_forearm_amplitude_rad
        self.human_forearm_period_s = human_forearm_period_s

        self._tick_handle: object | None = None
        self._zmq_session: UeZmqSession | None = None
        self._driver: Any = None
        self._cameras: list[dict] = []
        self._previous_sigint: Callable[..., Any] | int | None = None
        self._started = False

    def _ensure_sys_path(self) -> None:
        if self.python_parent is not None and str(self.python_parent) not in sys.path:
            sys.path.insert(0, str(self.python_parent))

    def _maybe_reload_modules(self) -> None:
        if not self.reload_senior_care_modules:
            return
        for mod_name in list(sys.modules):
            if mod_name.startswith("benchmark.senior_care"):
                try:
                    importlib.reload(sys.modules[mod_name])
                except Exception as exc:
                    unreal.log_warning(f"[UeEditorRunner] reload {mod_name} failed: {exc}")

    def stop(self, reason: str = "stop() called") -> None:
        unreal.log(f"[UeEditorRunner] stop: {reason}")

        h = getattr(unreal, "_senior_care_tick_handle", None)
        if h is not None:
            try:
                unreal.unregister_slate_pre_tick_callback(h)
            except Exception:
                pass
            unreal._senior_care_tick_handle = None  # type: ignore[attr-defined]
        elif self._tick_handle is not None:
            try:
                unreal.unregister_slate_pre_tick_callback(self._tick_handle)
            except Exception:
                pass
        self._tick_handle = None

        prev = getattr(unreal, "_senior_care_zmq_session", None)
        sess = prev if prev is not None else self._zmq_session
        if sess is not None:
            try:
                sess.close()
            except Exception:
                pass
            unreal._senior_care_zmq_session = None  # type: ignore[attr-defined]
        self._zmq_session = None
        self._started = False
        self._restore_sigint()

    def _on_sigint(self, signum: int, frame: FrameType | None) -> None:
        del signum, frame
        self.stop("SIGINT (Ctrl+C)")

    def _install_sigint(self) -> None:
        try:
            self._previous_sigint = signal.signal(signal.SIGINT, self._on_sigint)
        except ValueError:
            # Embedded interpreter may disallow handlers
            self._previous_sigint = None

    def _restore_sigint(self) -> None:
        if self._previous_sigint is not None:
            try:
                signal.signal(signal.SIGINT, self._previous_sigint)
            except ValueError:
                pass
            self._previous_sigint = None

    def start(self) -> None:
        """Load scene, open camera PUB if needed, register pre-tick callback."""
        self._ensure_sys_path()
        self._maybe_reload_modules()

        if not self.config_path.exists():
            unreal.log_error(f"[UeEditorRunner] config not found: {self.config_path!s}")
            return

        unreal.log(
            f"[UeEditorRunner] loading scene from {self.config_path!s} "
            f"(apply_initial_state={self.apply_initial_state}, "
            f"drive_test_joints={self.drive_test_joints}, "
            f"stream_cameras={self.stream_cameras})"
        )

        _scene, _loader, driver, cameras = load_scene_for_editor(
            self.config_path,
            apply_initial_state=self.apply_initial_state,
        )
        self._driver = driver
        self._cameras = cameras

        previous_handle = getattr(unreal, "_senior_care_tick_handle", None)
        if previous_handle is not None:
            try:
                unreal.unregister_slate_pre_tick_callback(previous_handle)
            except Exception:
                pass
            unreal._senior_care_tick_handle = None  # type: ignore[attr-defined]

        previous_zmq = getattr(unreal, "_senior_care_zmq_session", None)
        if previous_zmq is not None:
            try:
                previous_zmq.close()
            except Exception:
                pass
            unreal._senior_care_zmq_session = None  # type: ignore[attr-defined]

        zmq_session: UeZmqSession | None = None
        if cameras and self.stream_cameras:
            zmq_session = UeZmqSession()
            try:
                zmq_session.open_camera_pub(self.zmq_camera_address)
                unreal.log(
                    f"[UeEditorRunner] camera ZMQ PUB on {self.zmq_camera_address} "
                    f"({len(cameras)} camera(s): "
                    + ", ".join(c["spec"].name for c in cameras)
                    + ")"
                )
            except Exception as exc:
                unreal.log_error(f"[UeEditorRunner] camera ZMQ PUB failed: {exc}")
                zmq_session = None
        elif cameras and not self.stream_cameras:
            unreal.log(
                f"[UeEditorRunner] {len(cameras)} camera(s) spawned; STREAM_CAMERAS=False"
            )

        if not self.drive_test_joints and not (cameras and self.stream_cameras and zmq_session):
            unreal.log(
                "[UeEditorRunner] drive_test_joints=False and no camera stream; "
                "not registering tick callback."
            )
            self._zmq_session = zmq_session
            if zmq_session is not None:
                unreal._senior_care_zmq_session = zmq_session  # type: ignore[attr-defined]
            return

        callback = _build_tick_callback(
            driver,
            cameras,
            zmq_session,
            drive_test_joints=self.drive_test_joints,
            panda_amplitude_rad=self.panda_joint1_amplitude_rad,
            panda_period_s=self.panda_joint1_period_s,
            human_forearm_amplitude_rad=self.human_forearm_amplitude_rad,
            human_forearm_period_s=self.human_forearm_period_s,
            camera_capture_period_s=self.camera_capture_period_s,
        )
        handle = unreal.register_slate_pre_tick_callback(callback)
        self._tick_handle = handle
        unreal._senior_care_tick_handle = handle  # type: ignore[attr-defined]
        self._zmq_session = zmq_session
        unreal._senior_care_zmq_session = zmq_session  # type: ignore[attr-defined]

        self._install_sigint()

        self._started = True
        unreal.log("[UeEditorRunner] tick callback registered.")
        if self.drive_test_joints:
            unreal.log(
                "[UeEditorRunner] test joint motion enabled "
                f"(panda ±{self.panda_joint1_amplitude_rad} rad / {self.panda_joint1_period_s}s, "
                f"forearm ±{self.human_forearm_amplitude_rad} rad / {self.human_forearm_period_s}s)."
            )
        if cameras and self.stream_cameras and zmq_session is not None:
            unreal.log(
                f"[UeEditorRunner] camera streaming → {self.zmq_camera_address!s}."
            )
