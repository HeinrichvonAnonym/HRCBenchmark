"""MuJoCo-side ZMQ publisher – extracts simulation state and sends it to UE."""

from __future__ import annotations

import math
import re
from typing import TYPE_CHECKING, Any

from .human_cmd import HumanFrame
from .robot_cmd import RobotFrame
from .zmq_session import ZmqSession

if TYPE_CHECKING:
    import mujoco


def _normalize_joint_name(name: str) -> str:
    """Normalize MuJoCo joint names to match UE mapping conventions.

    MuJoCo SMPL-X model uses names like 'neck_ball', 'l_shoulder_ball'.
    The UE mapping expects 'neck', 'l_shoulder', etc.
    """
    return re.sub(r"_ball$", "", name)


def _quat_to_euler_xyz(quat: list[float]) -> list[float]:
    """Convert MuJoCo quaternion [w,x,y,z] to Euler angles [rx, ry, rz] (XYZ order).

    Returns intrinsic XYZ Euler angles in radians.
    """
    w, x, y, z = quat

    # Roll (x-axis rotation)
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    rx = math.atan2(sinr_cosp, cosr_cosp)

    # Pitch (y-axis rotation)
    sinp = 2.0 * (w * y - z * x)
    if abs(sinp) >= 1.0:
        ry = math.copysign(math.pi / 2.0, sinp)
    else:
        ry = math.asin(sinp)

    # Yaw (z-axis rotation)
    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    rz = math.atan2(siny_cosp, cosy_cosp)

    return [rx, ry, rz]


def _transform_joint_angle(axis_index: int, value: float) -> float:
    """Transform joint angle from MuJoCo to UE coordinate system.

    Coordinate transform T = diag(1, -1, 1) (only Y flips):
    - Rotation around X (index 0): X direction identical in both systems → unchanged
    - Rotation around Y (index 1): Y_mujoco = -Y_ue → negate
    - Rotation around Z (index 2): Z direction identical in both systems → unchanged
    """
    if axis_index == 1:  # Y axis only
        return -value
    else:  # X and Z are the same direction in both systems
        return value


class MujocoZmqSession(ZmqSession):
    """Wraps a ZMQ PUB socket that publishes per-step simulation state.

    Typical usage inside ``SeniorCareEnv``::

        self._zmq = MujocoZmqSession(address)
        self._zmq.open_pub()
        ...
        # each simulation step:
        self._zmq.publish_step(model, data, assets)
        ...
        self._zmq.close()

    Parameters
    ----------
    address : ZMQ bind address, e.g. ``tcp://*:5556``.
    """

    def __init__(self, address: str = "tcp://*:5556") -> None:
        super().__init__(address)
        self._seq = 0

    def publish_step(
        self,
        model: mujoco.MjModel,
        data: mujoco.MjData,
        assets: dict[str, Any],
    ) -> None:
        """Build a JSON frame from live MuJoCo state and send it.

        Parameters
        ----------
        model : The ``MjModel`` (needed to look up body names).
        data : Current ``MjData`` snapshot.
        assets : ``{name: AssetRuntime}`` dict from ``SeniorCareEnv``.

        The wire format matches what ``UeZmqSession.recv_frame`` expects::

            {
                "seq": int,
                "assets": {
                    "<name>": {
                        "root_position": [x, y, z],
                        "root_orientation": [w, x, y, z],
                        "joints": {"<joint>": float, ...},
                        "bone_transforms": {
                            "<body_name>": {
                                "position": [x, y, z],
                                "orientation": [w, x, y, z]
                            }
                        }
                    }
                }
            }
        """
        self._seq += 1
        assets_data: dict[str, dict] = {}

        for asset_name, asset in assets.items():
            root_pos: list[float] = data.xpos[asset.root_body_id].tolist()
            root_ori: list[float] = data.xquat[asset.root_body_id].tolist()

            joints: dict[str, float] = {}
            for channel in asset.observation_channels:
                val = channel.read_position(data.qpos)
                base_name = _normalize_joint_name(channel.name)
                if isinstance(val, list):
                    if len(val) == 4:
                        # Ball joint: quaternion [w,x,y,z] -> Euler XYZ
                        euler = _quat_to_euler_xyz(val)
                        for i, v in enumerate(euler):
                            transformed = _transform_joint_angle(i, v)
                            joints[f"{base_name}_{i}"] = float(transformed)
                    else:
                        # Other multi-DOF joint
                        for i, v in enumerate(val):
                            transformed = _transform_joint_angle(i, v)
                            joints[f"{base_name}_{i}"] = float(transformed)
                else:
                    joints[base_name] = float(val)

            bone_transforms: dict[str, dict[str, list[float]]] = {}
            for body_id in asset.subtree_body_ids:
                body_name = model.body(body_id).name
                bone_transforms[body_name] = {
                    "position": data.xpos[body_id].tolist(),
                    "orientation": data.xquat[body_id].tolist(),
                }

            frame_cls = HumanFrame if _is_human_asset(asset_name) else RobotFrame
            assets_data[asset_name] = frame_cls(
                root_position=root_pos,
                root_orientation=root_ori,
                joints=joints,
                bone_transforms=bone_transforms,
            ).to_dict()

        self.send_json({"seq": self._seq, "assets": assets_data})


def _is_human_asset(asset_name: str) -> bool:
    return any(keyword in asset_name.lower() for keyword in ("human", "smpl", "person", "body"))
