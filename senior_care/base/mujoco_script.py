from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
import re
import threading
import time
from typing import Any, Mapping, Sequence

from google.protobuf.message import DecodeError

import mujoco
import numpy as np
import yaml

from benchmark.senior_care.base.action import ActionMessage, AssetAction, zeros_from_selected_joints
from benchmark.senior_care.base.observation import AssetObservation, ObservationMessage
from benchmark.senior_care.base.scene.mujoco_scene import MujocoScene, attach_mujoco_asset_to_spec


WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = Path(__file__).resolve().parents[4]
_PACKAGE_URI_PATTERN = re.compile(r"package://([^/]+)/")


_LOG = logging.getLogger(__name__)

_DEFAULT_FRANKA_CMD_TOPIC = "franka/command"
_DEFAULT_FRANKA_STATE_TOPIC = "franka/state"

CMD_TOPIC_DEFAULT = _DEFAULT_FRANKA_CMD_TOPIC
STATE_TOPIC_DEFAULT = _DEFAULT_FRANKA_STATE_TOPIC


class _ZenohFrankaCmdBuffer:
    """Thread-safe store for the latest franka RobotCommand joint targets (wire format)."""

    def __init__(self, franka_pb2_module: Any) -> None:
        self._pb = franka_pb2_module
        self._lock = threading.Lock()
        self._q7: tuple[float, ...] | None = None
        self._last_cmd_mode = "position"

    def ingest(
        self, raw: bytes
    ) -> tuple[str, tuple[float, ...] | None, int, int, str]:
        cmd = self._pb.RobotCommand()
        try:
            cmd.ParseFromString(raw)
        except DecodeError:
            return ("protobuf_decode_failed", None, 0, 0, "")
        nj = len(cmd.joints)
        if nj != 7:
            return (f"joints_need_7_got_{nj}", None, 0, 0, "")
        q = tuple(float(cmd.joints[i].position) for i in range(7))
        md = (cmd.mode or "").strip() or "position"
        with self._lock:
            self._q7 = q
            self._last_cmd_mode = md
        return ("ok", q, int(cmd.type), int(cmd.sequence), cmd.mode or "")

    def arm_targets(self) -> tuple[float, ...] | None:
        with self._lock:
            return self._q7

    def state_mode_label(self) -> str:
        with self._lock:
            return self._last_cmd_mode


def _zenoh_payload_to_bytes(payload: object) -> bytes:
    if hasattr(payload, "to_bytes"):
        return payload.to_bytes()  # type: ignore[no-any-return]
    if isinstance(payload, (bytes, bytearray)):
        return bytes(payload)
    return bytes(payload)  # type: ignore[arg-type]


@dataclass(frozen=True)
class JointChannel:
    name: str
    actual_joint_names: tuple[str, ...]
    qpos_indices: tuple[int, ...]
    qvel_indices: tuple[int, ...]
    dof_indices: tuple[int, ...]
    command_mode: str = "direct"

    def set_target_position(self, target_qpos: np.ndarray, value: float | Sequence[float]) -> None:
        if self.command_mode == "gripper_width":
            width = float(value)
            finger_value = 0.5 * width
            for qpos_index in self.qpos_indices:
                target_qpos[qpos_index] = finger_value
            return

        values = _coerce_vector(value, len(self.qpos_indices), f"{self.name} position")
        for qpos_index, entry in zip(self.qpos_indices, values):
            target_qpos[qpos_index] = entry

    def set_initial_velocity(self, qvel: np.ndarray, value: float | Sequence[float]) -> None:
        if self.command_mode == "gripper_width":
            width_rate = float(value)
            finger_rate = 0.5 * width_rate
            for qvel_index in self.qvel_indices:
                qvel[qvel_index] = finger_rate
            return

        values = _coerce_vector(value, len(self.qvel_indices), f"{self.name} velocity")
        for qvel_index, entry in zip(self.qvel_indices, values):
            qvel[qvel_index] = entry

    def set_initial_effort(self, qfrc_applied: np.ndarray, value: float | Sequence[float]) -> None:
        if self.command_mode == "gripper_width":
            width_effort = float(value)
            finger_effort = 0.5 * width_effort
            for dof_index in self.dof_indices:
                qfrc_applied[dof_index] = finger_effort
            return

        values = _coerce_vector(value, len(self.dof_indices), f"{self.name} effort")
        for dof_index, entry in zip(self.dof_indices, values):
            qfrc_applied[dof_index] = entry

    def copy_from_qpos(self, target_qpos: np.ndarray, source_qpos: np.ndarray) -> None:
        for qpos_index in self.qpos_indices:
            target_qpos[qpos_index] = source_qpos[qpos_index]

    def read_position(self, qpos: np.ndarray) -> float | list[float]:
        values = [float(qpos[qpos_index]) for qpos_index in self.qpos_indices]
        if self.command_mode == "gripper_width":
            return float(sum(values))
        return _pack_output(values)

    def read_velocity(self, qvel: np.ndarray) -> float | list[float]:
        values = [float(qvel[qvel_index]) for qvel_index in self.qvel_indices]
        if self.command_mode == "gripper_width":
            return float(sum(values))
        return _pack_output(values)

    def read_effort(self, qfrc_applied: np.ndarray) -> float | list[float]:
        values = [float(qfrc_applied[dof_index]) for dof_index in self.dof_indices]
        if self.command_mode == "gripper_width":
            return float(sum(values))
        return _pack_output(values)


@dataclass
class AssetRuntime:
    name: str
    config: dict[str, Any]
    root_body_name: str
    root_body_id: int
    subtree_body_ids: tuple[int, ...]
    actual_joint_channels: dict[str, JointChannel]
    selected_channels: list[JointChannel]
    observation_channels: list[JointChannel]
    unspecified_actual_channels: list[JointChannel]
    kp: list[float]
    kd: list[float]
    hold_kp: float
    hold_kd: float
    behavior_of_unspecified: str
    initial_qpos: np.ndarray | None = field(default=None, repr=False)


class SeniorCareEnv:
    def __init__(
        self,
        config_path: str | Path,
        *,
        zenoh_publish: bool = False,
        zenoh_franka_topics: bool = True,
        zenoh_cmd_topic: str = _DEFAULT_FRANKA_CMD_TOPIC,
        zenoh_state_topic: str = _DEFAULT_FRANKA_STATE_TOPIC,
        zenoh_connect_endpoints: Sequence[str] | None = None,
        zmq_publish: bool = False,
        zmq_address: str = "tcp://localhost:5556",
        view_camera: bool = False,
        zmq_camera_address: str = "tcp://localhost:5557",
    ) -> None:
        self.config_path = self._resolve_path(config_path)
        self.config = yaml.safe_load(self.config_path.read_text()) or {}
        self.dt = _parse_dt(self.config.get("dt", 1 / 120))
        self.observation_asset_names = list(self.config.get("observation", []))
        self.action_asset_names = list(self.config.get("action", []))
        self.assets: dict[str, AssetRuntime] = {}

        self._zenoh_publish = zenoh_publish
        self._zenoh_franka_topics = zenoh_franka_topics
        self._zenoh_cmd_topic = str(zenoh_cmd_topic)
        self._zenoh_state_topic = str(zenoh_state_topic)
        self._zenoh_connect_endpoints = list(zenoh_connect_endpoints or [])

        self._zenoh_session = None
        self._zenoh_sub_handles: list[Any] = []
        self._zenoh_pub_franka_cmd = None
        self._zenoh_pub_franka_state_legacy = None
        self._zenoh_pub_wire_franka_state = None
        self._zenoh_pub_human = None
        self._zenoh_seq = 0
        self._franka_wire_state_seq = 0
        self._franka_pb2 = None
        self._demo_inference_pb2 = None
        self._franka_cmd_buf: _ZenohFrankaCmdBuffer | None = None
        self._franka_zenoh_asset: str | None = None
        self._human_zenoh_asset: str | None = None

        self._zmq_session: Any | None = None
        self._view_camera = view_camera

        self.scene: MujocoScene | None = None
        self.model = self._build_model()
        self.data = mujoco.MjData(self.model)
        self.selected_joints = {
            asset_name: list(self.assets[asset_name].config.get("action", {}).get("selected_joints", []))
            for asset_name in self.action_asset_names
            if asset_name in self.assets
        }
        self._pick_zenoh_asset_names()
        self.reset()

        if self._zenoh_franka_topics or self._zenoh_publish:
            self._setup_zenoh()
        if zmq_publish:
            from benchmark.senior_care.ue_mujoco_bridge import MujocoZmqSession

            self._zmq_session = MujocoZmqSession(zmq_address)
            self._zmq_session.open_pub()
            if view_camera:
                self._zmq_session.open_camera_sub(zmq_camera_address)

    def reset(self) -> dict[str, dict[str, object]]:
        self.data = mujoco.MjData(self.model)
        self.data.qfrc_applied[:] = 0.0

        for asset in self.assets.values():
            self._apply_initial_state(asset)

        mujoco.mj_forward(self.model, self.data)

        for asset in self.assets.values():
            asset.initial_qpos = self.data.qpos.copy()

        return self._build_observation().to_dict()

    def home_action(self) -> dict[str, dict[str, dict[str, float]]]:
        """Return an action dict that commands each asset to its initial (home) position from the YAML."""
        result: dict[str, dict[str, dict[str, float]]] = {}
        for asset_name in self.action_asset_names:
            asset = self.assets.get(asset_name)
            if asset is None or asset.initial_qpos is None:
                continue
            position: dict[str, float] = {}
            for channel in asset.selected_channels:
                position[channel.name] = channel.read_position(asset.initial_qpos)
            result[asset_name] = {"position": position}
        return result


    def step(self, action: Mapping[str, Any] | ActionMessage) -> dict[str, dict[str, object]]:
        action_message = ActionMessage.from_any(action)
        if self._zenoh_franka_topics and self._franka_cmd_buf is not None:
            self._overlay_zenoh_franka_targets(action_message)
        commanded_qpos = self.data.qpos.copy()
        applied_force = np.zeros(self.model.nv, dtype=float)

        for asset_name in self.action_asset_names:
            asset = self.assets[asset_name]
            asset_action = action_message.assets.get(
                asset_name,
                AssetAction(position={ch.name: 0.0 for ch in asset.selected_channels}),
            )

            for channel in asset.selected_channels:
                target = asset_action.position.get(channel.name, 0.0)
                channel.set_target_position(commanded_qpos, target)

            if asset.behavior_of_unspecified == "fix":
                if asset.initial_qpos is None:
                    raise RuntimeError("Environment must be reset before stepping.")
                for channel in asset.unspecified_actual_channels:
                    channel.copy_from_qpos(commanded_qpos, asset.initial_qpos)

        position_error = np.zeros(self.model.nv, dtype=float)
        mujoco.mj_differentiatePos(self.model, position_error, 1.0, self.data.qpos, commanded_qpos)

        for asset_name in self.action_asset_names:
            asset = self.assets[asset_name]
            asset_action = action_message.assets.get(
                asset_name,
                AssetAction(position={ch.name: 0.0 for ch in asset.selected_channels}),
            )

            for channel, kp_value, kd_value in zip(asset.selected_channels, asset.kp, asset.kd):
                for dof_index in channel.dof_indices:
                    applied_force[dof_index] = (
                        kp_value * position_error[dof_index] - kd_value * self.data.qvel[dof_index]
                    )

            if asset.behavior_of_unspecified == "fix":
                for channel in asset.unspecified_actual_channels:
                    for dof_index in channel.dof_indices:
                        applied_force[dof_index] = (
                            asset.hold_kp * position_error[dof_index]
                            - asset.hold_kd * self.data.qvel[dof_index]
                        )

        self.data.qfrc_applied[:] = applied_force
        mujoco.mj_step(self.model, self.data)
        obs_dict = self._build_observation().to_dict()
        if self._zenoh_pub_wire_franka_state is not None and self._franka_pb2 is not None:
            self._publish_wire_franka_state()
        if self._zenoh_publish:
            self._zenoh_publish_step(action_message)
        if self._zmq_session is not None:
            self._zmq_session.publish_step(self.model, self.data, self.assets)
        if self._view_camera and self._zmq_session is not None:
            camera_frame = self._zmq_session.recv_camera_frame()
            if camera_frame is not None:
                self._show_camera_frame(camera_frame)
        return obs_dict

    def close(self) -> None:
        if self._zenoh_session is not None:
            self._zenoh_session.close()
            self._zenoh_session = None
        self._zenoh_sub_handles.clear()
        self._zenoh_pub_franka_cmd = None
        self._zenoh_pub_franka_state_legacy = None
        self._zenoh_pub_wire_franka_state = None
        self._zenoh_pub_human = None
        self._franka_cmd_buf = None
        if self._zmq_session is not None:
            self._zmq_session.close()
            self._zmq_session = None

    def _show_camera_frame(self, frame: Any) -> None:
        """Display an RGBD camera frame in OpenCV windows.

        Shows two windows per camera:
        - ``[RGB] <name>`` — colour image (BGR for OpenCV).
        - ``[Depth] <name>`` — depth normalised to uint8 for visualisation;
          black = no geometry (sky / beyond far-plane), bright = close.

        Requires ``opencv-python`` (``pip install opencv-python``).
        Silently skips if cv2 is not installed.
        """
        try:
            import cv2
        except ImportError:
            _LOG.warning(
                "[SeniorCareEnv] view_camera=True but 'opencv-python' is not "
                "installed; skipping camera display. "
                "Install with: pip install opencv-python"
            )
            self._view_camera = False  # suppress repeated warnings
            return

        rgb = frame.rgb_array()  # (H, W, 3) uint8, RGB order
        rgb_bgr = rgb[..., ::-1]  # flip to BGR for OpenCV
        cv2.imshow(f"[RGB] {frame.camera_name}", rgb_bgr)

        depth = frame.depth_array()  # (H, W) float32, metres
        valid = depth > 0.0
        d_vis = np.zeros(depth.shape, dtype=np.uint8)
        if valid.any():
            d_min = float(depth[valid].min())
            d_max = float(depth[valid].max())
            if d_max > d_min:
                d_vis[valid] = (
                    (depth[valid] - d_min) / (d_max - d_min) * 255
                ).astype(np.uint8)
        cv2.imshow(f"[Depth] {frame.camera_name}", d_vis)
        cv2.waitKey(1)

    def _pick_zenoh_asset_names(self) -> None:
        for name in self.action_asset_names:
            if name in self.assets and self.assets[name].selected_channels:
                self._franka_zenoh_asset = name
                break
        if "simpl_neutral" in self.assets:
            self._human_zenoh_asset = "simpl_neutral"

    def _overlay_zenoh_franka_targets(self, action_message: ActionMessage) -> None:
        name = self._franka_zenoh_asset
        if name is None or self._franka_cmd_buf is None:
            return
        q7 = self._franka_cmd_buf.arm_targets()
        if q7 is None:
            return
        aa = action_message.assets.get(name)
        if aa is None:
            asset_rt = self.assets[name]
            aa = AssetAction(position={ch.name: 0.0 for ch in asset_rt.selected_channels})
            action_message.assets[name] = aa
        asset_rt = self.assets[name]
        for i, channel in enumerate(asset_rt.selected_channels[:7]):
            aa.position[channel.name] = float(q7[i])

    def _publish_wire_franka_state(self) -> None:
        franka_name = self._franka_zenoh_asset
        if franka_name is None:
            return
        assert self._franka_pb2 is not None
        assert self._zenoh_pub_wire_franka_state is not None
        assert self._franka_cmd_buf is not None
        pb = self._franka_pb2
        asset = self.assets[franka_name]
        arm_channels = asset.selected_channels[:7]
        obs = pb.RobotObservation()
        obs.type = 2
        self._franka_wire_state_seq += 1
        obs.sequence = self._franka_wire_state_seq
        obs.mode = self._franka_cmd_buf.state_mode_label()
        obs.note = "senior_care_mujoco_wire"
        obs.sys_time = float(self.data.time)
        obs.ClearField("joints")
        for ch in arm_channels:
            jo = obs.joints.add()
            jo.position = _scalar_for_zenoh(ch.read_position(self.data.qpos))
            jo.velocity = _scalar_for_zenoh(ch.read_velocity(self.data.qvel))
            jo.effort = _scalar_for_zenoh(ch.read_effort(self.data.qfrc_applied))
        while len(obs.joints) < 7:
            jo = obs.joints.add()
            jo.position = 0.0
            jo.velocity = 0.0
            jo.effort = 0.0
        self._zenoh_pub_wire_franka_state.put(obs.SerializeToString())

    def _setup_zenoh(self) -> None:
        os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

        try:
            import zenoh
        except ImportError as e:
            raise RuntimeError(
                "Zenoh-enabled SeniorCareEnv requires eclipse-zenoh (pip install eclipse-zenoh). "
                "Pass zenoh_franka_topics=False and zenoh_publish=False to disable Zenoh.",
            ) from e

        from robo_lab.proto_gen import franka_pb2 as fr_pb2_mod

        self._franka_pb2 = fr_pb2_mod

        conf = zenoh.Config()
        if os.environ.get("ROBO_LAB_ZENOH_MULTICAST_SCOUTING") == "0":
            conf.insert_json5("scouting/multicast/enabled", json.dumps(False))
        if self._zenoh_connect_endpoints:
            conf.insert_json5("connect/endpoints", json.dumps(self._zenoh_connect_endpoints))

        session = zenoh.open(conf)
        self._zenoh_session = session

        cmd_tag = self._zenoh_cmd_topic
        legacy_franka_echo = self._zenoh_publish and not self._zenoh_franka_topics

        if self._zenoh_franka_topics:
            buf = _ZenohFrankaCmdBuffer(fr_pb2_mod)
            self._franka_cmd_buf = buf
            self._franka_wire_state_seq = 0

            def _on_wire_cmd(sample: Any) -> None:
                raw = _zenoh_payload_to_bytes(sample.payload)
                log = _LOG
                if log.isEnabledFor(logging.INFO):
                    log.info(
                        "[%s] recv key_expr=%s nbytes=%d",
                        cmd_tag,
                        str(sample.key_expr),
                        len(raw),
                    )
                reason, q7, cmd_type, sequence, modestr = buf.ingest(raw)
                if reason != "ok":
                    log.warning("[%s] not applied: %s (nbytes=%d)", cmd_tag, reason, len(raw))
                    return
                assert q7 is not None
                log.info(
                    "[%s] applied type=%s seq=%s mode=%r q[:3]=%s q[4:7]=%s",
                    cmd_tag,
                    cmd_type,
                    sequence,
                    modestr,
                    [round(q7[i], 4) for i in range(3)],
                    [round(q7[i], 4) for i in range(4, 7)],
                )

            self._zenoh_sub_handles.append(session.declare_subscriber(self._zenoh_cmd_topic, _on_wire_cmd))
            self._zenoh_pub_wire_franka_state = session.declare_publisher(self._zenoh_state_topic)

        if self._zenoh_publish:
            human_ok = self._human_zenoh_asset is not None
            if human_ok:
                from robo_lab.proto_gen import demo_inference_pb2 as di_pb2

                self._demo_inference_pb2 = di_pb2
                self._zenoh_pub_human = session.declare_publisher("HumanState")
            else:
                self._demo_inference_pb2 = None
                self._zenoh_pub_human = None

            if legacy_franka_echo:
                self._zenoh_pub_franka_cmd = session.declare_publisher(self._zenoh_cmd_topic)
                self._zenoh_pub_franka_state_legacy = session.declare_publisher(self._zenoh_state_topic)
            else:
                self._zenoh_pub_franka_cmd = None
                self._zenoh_pub_franka_state_legacy = None
        else:
            self._demo_inference_pb2 = None
            self._zenoh_pub_human = None
            self._zenoh_pub_franka_cmd = None
            self._zenoh_pub_franka_state_legacy = None

    def _zenoh_publish_step(self, action_message: ActionMessage) -> None:
        assert self._franka_pb2 is not None
        self._zenoh_seq += 1
        seq = self._zenoh_seq
        t_wall = time.time()
        pb = self._franka_pb2

        franka_name = self._franka_zenoh_asset
        if franka_name is not None and self._zenoh_pub_franka_cmd is not None:
            assert self._zenoh_pub_franka_state_legacy is not None
            asset = self.assets[franka_name]
            asset_action = action_message.assets.get(
                franka_name,
                AssetAction(position={ch.name: 0.0 for ch in asset.selected_channels}),
            )
            arm_channels = asset.selected_channels[:7]
            cmd = pb.RobotCommand()
            cmd.type = 2
            cmd.sequence = seq
            cmd.mode = "position"
            cmd.note = "senior_care_mujoco"
            cmd.sys_time = float(t_wall)
            cmd.ClearField("joints")
            for ch in arm_channels:
                jc = cmd.joints.add()
                raw = asset_action.position.get(ch.name, 0.0)
                jc.position = _scalar_for_zenoh(raw)
                jc.velocity = 0.0
                jc.effort = 0.0
            while len(cmd.joints) < 7:
                jc = cmd.joints.add()
                jc.position = 0.0
                jc.velocity = 0.0
                jc.effort = 0.0
            self._zenoh_pub_franka_cmd.put(cmd.SerializeToString())

            obs_msg = pb.RobotObservation()
            obs_msg.type = 2
            obs_msg.sequence = seq
            obs_msg.mode = "position"
            obs_msg.note = "senior_care_mujoco"
            obs_msg.sys_time = float(t_wall)
            obs_msg.ClearField("joints")
            for ch in arm_channels:
                jo = obs_msg.joints.add()
                jo.position = _scalar_for_zenoh(ch.read_position(self.data.qpos))
                jo.velocity = _scalar_for_zenoh(ch.read_velocity(self.data.qvel))
                jo.effort = _scalar_for_zenoh(ch.read_effort(self.data.qfrc_applied))
            while len(obs_msg.joints) < 7:
                jo = obs_msg.joints.add()
                jo.position = 0.0
                jo.velocity = 0.0
                jo.effort = 0.0
            self._zenoh_pub_franka_state_legacy.put(obs_msg.SerializeToString())

        human_name = self._human_zenoh_asset
        if human_name is not None and self._zenoh_pub_human is not None:
            assert self._demo_inference_pb2 is not None
            hasset = self.assets[human_name]
            human_obs = self._demo_inference_pb2.Observation()
            flat: list[float] = []
            for ch in hasset.observation_channels:
                pos = ch.read_position(self.data.qpos)
                if isinstance(pos, list):
                    flat.extend(float(x) for x in pos)
                else:
                    flat.append(float(pos))
            if len(flat) >= _HUMAN_STATE_DIM:
                flat = flat[:_HUMAN_STATE_DIM]
            else:
                flat.extend([0.0] * (_HUMAN_STATE_DIM - len(flat)))
            human_obs.values.extend(flat)
            self._zenoh_pub_human.put(human_obs.SerializeToString())

    def _build_model(self) -> mujoco.MjModel:
        main_spec = mujoco.MjSpec.from_string(
            f'<mujoco model="senior_care"><option timestep="{self.dt}"/><worldbody/></mujoco>'
        )

        ground = main_spec.worldbody.add_geom()
        ground.name = "ground"
        ground.type = mujoco.mjtGeom.mjGEOM_PLANE
        ground.size = [0, 0, 0.05]
        ground.rgba = [0.9, 0.9, 0.9, 1.0]
        ground.contype = 1
        ground.conaffinity = 1

        scene_rel = self.config.get("scene_config")
        if scene_rel:
            scene_path = self._resolve_path(str(scene_rel))
            self.scene = MujocoScene.from_yaml_path(scene_path)
            self.scene.attach_into(
                main_spec,
                resolve_path=self._resolve_path,
                load_asset_spec=self._load_asset_spec,
            )
        else:
            self.scene = None

        asset_configs = self.config.get("assets", [])
        for asset_config in asset_configs:
            attach_mujoco_asset_to_spec(
                main_spec,
                asset_config,
                resolve_path=self._resolve_path,
                load_asset_spec=self._load_asset_spec,
            )

        model = main_spec.compile()

        for asset_config in asset_configs:
            model_path = asset_config.get("mujoco_model")
            if not model_path:
                continue

            asset = self._build_asset_runtime(model, asset_config)
            self.assets[asset.name] = asset

            if asset_config.get("disable_gravity", False):
                for body_id in asset.subtree_body_ids:
                    model.body_gravcomp[body_id] = 1.0

        return model

    def _build_asset_runtime(self, model: mujoco.MjModel, asset_config: dict[str, Any]) -> AssetRuntime:
        root_body_name = str(asset_config.get("frame"))
        root_body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, root_body_name)
        if root_body_id < 0:
            raise ValueError(
                f"Asset '{asset_config['name']}' uses root body '{root_body_name}', but it was not found."
            )

        subtree_body_ids = _collect_subtree_body_ids(model, root_body_id)
        actual_joint_channels = _build_actual_joint_channels(model, subtree_body_ids)

        action_config = asset_config.get("action", {})
        selected_joint_names = list(action_config.get("selected_joints", []))
        selected_channels = [
            self._resolve_selected_channel(asset_config["name"], joint_name, actual_joint_channels)
            for joint_name in selected_joint_names
        ]
        selected_actual_joint_names = {
            actual_joint_name
            for channel in selected_channels
            for actual_joint_name in channel.actual_joint_names
        }
        unspecified_actual_channels = [
            channel
            for joint_name, channel in actual_joint_channels.items()
            if joint_name not in selected_actual_joint_names
        ]

        kp = [float(value) for value in action_config.get("kp", [])]
        kd = [float(value) for value in action_config.get("kd", [])]
        if len(kp) != len(selected_channels) or len(kd) != len(selected_channels):
            raise ValueError(
                f"Asset '{asset_config['name']}' must provide one kp and one kd per selected joint."
            )

        hold_kp = float(kp[0]) if kp else 50.0
        hold_kd = float(kd[0]) if kd else 5.0
        behavior_of_unspecified = str(action_config.get("behavior_of_unspecified", "free")).lower()
        if behavior_of_unspecified not in {"fix", "free"}:
            raise ValueError(
                f"Asset '{asset_config['name']}' has invalid behavior_of_unspecified: "
                f"{behavior_of_unspecified}"
            )

        observation_channels = selected_channels or list(actual_joint_channels.values())

        return AssetRuntime(
            name=str(asset_config["name"]),
            config=asset_config,
            root_body_name=root_body_name,
            root_body_id=root_body_id,
            subtree_body_ids=subtree_body_ids,
            actual_joint_channels=actual_joint_channels,
            selected_channels=selected_channels,
            observation_channels=observation_channels,
            unspecified_actual_channels=unspecified_actual_channels,
            kp=kp,
            kd=kd,
            hold_kp=hold_kp,
            hold_kd=hold_kd,
            behavior_of_unspecified=behavior_of_unspecified,
        )

    def _apply_initial_state(self, asset: AssetRuntime) -> None:
        state_config = asset.config.get("state", {})

        initial_position = list(state_config.get("position", {}).get("initial", []))
        if initial_position:
            self._try_apply_sequence(initial_position, asset, "position")

        initial_velocity = list(state_config.get("velocity", {}).get("initial", []))
        if initial_velocity:
            self._try_apply_sequence(initial_velocity, asset, "velocity")

        initial_effort = list(state_config.get("effort", {}).get("initial", []))
        if initial_effort:
            self._try_apply_sequence(initial_effort, asset, "effort")

    def _try_apply_sequence(self, values: Sequence[float], asset: AssetRuntime, mode: str) -> bool:
        channel_groups = [asset.selected_channels, list(asset.actual_joint_channels.values())]

        for channels in channel_groups:
            if not channels:
                continue

            if len(values) != len(channels):
                continue
            if any(len(channel.qpos_indices) != 1 and channel.command_mode == "direct" for channel in channels):
                continue

            for channel, value in zip(channels, values):
                if mode == "position":
                    channel.set_target_position(self.data.qpos, float(value))
                elif mode == "velocity":
                    channel.set_initial_velocity(self.data.qvel, float(value))
                elif mode == "effort":
                    channel.set_initial_effort(self.data.qfrc_applied, float(value))
            return True

        return False

    def _build_observation(self) -> ObservationMessage:
        assets: dict[str, AssetObservation] = {}

        for asset_name in self.observation_asset_names:
            asset = self.assets[asset_name]
            assets[asset_name] = AssetObservation(
                root_position=self.data.xpos[asset.root_body_id].tolist(),
                root_orientation=self.data.xquat[asset.root_body_id].tolist(),
                position={
                    channel.name: channel.read_position(self.data.qpos)
                    for channel in asset.observation_channels
                },
                velocity={
                    channel.name: channel.read_velocity(self.data.qvel)
                    for channel in asset.observation_channels
                },
                effort={
                    channel.name: channel.read_effort(self.data.qfrc_applied)
                    for channel in asset.observation_channels
                },
            )

        return ObservationMessage(assets=assets)

    def _load_asset_spec(self, model_path: str | Path) -> mujoco.MjSpec:
        resolved_path = self._resolve_path(model_path)
        file_text = resolved_path.read_text()
        is_urdf = resolved_path.suffix.lower() == ".urdf" or "<robot" in file_text[:256]

        if not is_urdf:
            return mujoco.MjSpec.from_file(str(resolved_path))

        def _replace_package_uri(match: re.Match[str]) -> str:
            package_name = match.group(1)
            package_path = self._resolve_package_path(package_name, resolved_path)
            return f"{package_path.as_posix()}/"

        urdf_text = _PACKAGE_URI_PATTERN.sub(_replace_package_uri, file_text)
        return mujoco.MjSpec.from_string(urdf_text)

    def _resolve_package_path(self, package_name: str, model_path: Path) -> Path:
        candidates = [
            model_path.parent.parent / package_name,
            WORKSPACE_ROOT / "benchmark/asset/robot" / package_name,
            REPO_ROOT / "python/benchmark/asset/robot" / package_name,
            REPO_ROOT / package_name,
        ]

        for candidate in candidates:
            if candidate.exists():
                return candidate

        raise FileNotFoundError(f"Could not resolve package://{package_name}/ for {model_path}")

    def _resolve_path(self, raw_path: str | Path) -> Path:
        candidate = Path(raw_path)
        if candidate.is_absolute() and candidate.exists():
            return candidate

        search_roots = [self.config_path.parent] if hasattr(self, "config_path") else []
        search_roots.extend([WORKSPACE_ROOT, REPO_ROOT])

        for root in search_roots:
            resolved = root / candidate
            if resolved.exists():
                return resolved

        raise FileNotFoundError(f"Path not found: {raw_path}")

    def _resolve_selected_channel(
        self,
        asset_name: str,
        joint_name: str,
        actual_joint_channels: Mapping[str, JointChannel],
    ) -> JointChannel:
        direct_channel = actual_joint_channels.get(joint_name)
        if direct_channel is not None:
            return direct_channel

        if joint_name == "panda_hand_joint":
            finger_joint_names = ("panda_finger_joint1", "panda_finger_joint2")
            if all(name in actual_joint_channels for name in finger_joint_names):
                qpos_indices = tuple(
                    index
                    for name in finger_joint_names
                    for index in actual_joint_channels[name].qpos_indices
                )
                qvel_indices = tuple(
                    index
                    for name in finger_joint_names
                    for index in actual_joint_channels[name].qvel_indices
                )
                dof_indices = tuple(
                    index
                    for name in finger_joint_names
                    for index in actual_joint_channels[name].dof_indices
                )
                return JointChannel(
                    name=joint_name,
                    actual_joint_names=finger_joint_names,
                    qpos_indices=qpos_indices,
                    qvel_indices=qvel_indices,
                    dof_indices=dof_indices,
                    command_mode="gripper_width",
                )

        raise ValueError(f"Asset '{asset_name}' selected joint '{joint_name}' was not found in MuJoCo.")


def _build_actual_joint_channels(
    model: mujoco.MjModel,
    subtree_body_ids: Sequence[int],
) -> dict[str, JointChannel]:
    subtree_body_set = set(subtree_body_ids)
    channels: dict[str, JointChannel] = {}

    for joint_id in range(model.njnt):
        joint_name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, joint_id)
        if not joint_name:
            continue
        if model.jnt_bodyid[joint_id] not in subtree_body_set:
            continue
        if model.jnt_type[joint_id] == mujoco.mjtJoint.mjJNT_FREE:
            continue

        qpos_dim = _joint_qpos_dim(model.jnt_type[joint_id])
        dof_dim = _joint_dof_dim(model.jnt_type[joint_id])
        qpos_start = model.jnt_qposadr[joint_id]
        dof_start = model.jnt_dofadr[joint_id]

        channels[joint_name] = JointChannel(
            name=joint_name,
            actual_joint_names=(joint_name,),
            qpos_indices=tuple(range(qpos_start, qpos_start + qpos_dim)),
            qvel_indices=tuple(range(dof_start, dof_start + dof_dim)),
            dof_indices=tuple(range(dof_start, dof_start + dof_dim)),
        )

    return channels


def _collect_subtree_body_ids(model: mujoco.MjModel, root_body_id: int) -> tuple[int, ...]:
    body_children: dict[int, list[int]] = {}
    for body_id in range(1, model.nbody):
        parent_id = int(model.body_parentid[body_id])
        body_children.setdefault(parent_id, []).append(body_id)

    ordered_body_ids: list[int] = []
    stack = [root_body_id]

    while stack:
        body_id = stack.pop()
        ordered_body_ids.append(body_id)
        children = body_children.get(body_id, [])
        stack.extend(reversed(children))

    return tuple(ordered_body_ids)


def _joint_qpos_dim(joint_type: int) -> int:
    if joint_type == mujoco.mjtJoint.mjJNT_BALL:
        return 4
    if joint_type == mujoco.mjtJoint.mjJNT_FREE:
        return 7
    return 1


def _joint_dof_dim(joint_type: int) -> int:
    if joint_type == mujoco.mjtJoint.mjJNT_BALL:
        return 3
    if joint_type == mujoco.mjtJoint.mjJNT_FREE:
        return 6
    return 1


def _parse_dt(raw_value: Any) -> float:
    if isinstance(raw_value, str):
        return float(Fraction(raw_value))
    return float(raw_value)


def _coerce_vector(
    raw_value: float | Sequence[float],
    expected_size: int,
    label: str,
) -> list[float]:
    if isinstance(raw_value, Sequence) and not isinstance(raw_value, (str, bytes)):
        values = [float(entry) for entry in raw_value]
    else:
        values = [float(raw_value)]

    if len(values) != expected_size:
        raise ValueError(f"{label} expects {expected_size} values, received {len(values)}.")

    return values


def _pack_output(values: Sequence[float]) -> float | list[float]:
    if len(values) == 1:
        return float(values[0])
    return [float(value) for value in values]


def _scalar_for_zenoh(value: float | list[float]) -> float:
    if isinstance(value, list):
        return float(value[0]) if value else 0.0
    return float(value)


_HUMAN_STATE_DIM = 19


def _rotvec_to_quat(rotvec: Sequence[float]) -> list[float]:
    x, y, z = [float(v) for v in rotvec]
    angle = float(np.sqrt(x * x + y * y + z * z))
    if angle < 1e-12:
        return [1.0, 0.0, 0.0, 0.0]
    half = 0.5 * angle
    s = float(np.sin(half) / angle)
    return [float(np.cos(half)), x * s, y * s, z * s]