"""MuJoCo-side ZMQ publisher – extracts simulation state and sends it to UE."""

from __future__ import annotations

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

    # Diagnostic: log ball-joint details every N frames (None to disable).
    DIAG_LOG_EVERY = 120  # roughly once per second at 120Hz
    # Which human joints to log in detail (bone tokens, not "_ball" suffix).
    DIAG_JOINT_NAMES: tuple[str, ...] = (
        "l_shoulder", "r_shoulder", "l_elbow", "r_elbow", "neck",
    )

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
        should_diag_log = (
            self.DIAG_LOG_EVERY is not None
            and self._seq % self.DIAG_LOG_EVERY == 0
        )

        for asset_name, asset in assets.items():
            root_pos: list[float] = data.xpos[asset.root_body_id].tolist()
            root_ori: list[float] = data.xquat[asset.root_body_id].tolist()

            is_human_for_diag = _is_human_asset(asset_name) and should_diag_log
            diag_lines: list[str] = []

            joints: dict[str, float] = {}
            for channel in asset.observation_channels:
                val = channel.read_position(data.qpos)
                base_name = _normalize_joint_name(channel.name)
                if isinstance(val, list):
                    if len(val) == 4:
                        # Ball joint: quaternion [w,x,y,z] in MuJoCo's
                        # right-handed Z-up frame.  Pass the raw values
                        # straight through; the C++ bridge does the proper
                        # RH→LH handedness conversion (negate x and z, keep y)
                        # in one place.
                        w, x, y, z = val
                        joints[f"{base_name}_w"] = float(w)
                        joints[f"{base_name}_x"] = float(x)
                        joints[f"{base_name}_y"] = float(y)
                        joints[f"{base_name}_z"] = float(z)
                        if is_human_for_diag and base_name in self.DIAG_JOINT_NAMES:
                            diag_lines.append(
                                f"  {base_name}: quat_mujoco=("
                                f"{w:+.3f},{x:+.3f},{y:+.3f},{z:+.3f}) "
                                f"-> quat_ue=({w:+.3f},{-x:+.3f},{y:+.3f},{-z:+.3f}) [done in C++]"
                            )
                    else:
                        # Other multi-DOF joint (rare)
                        for i, v in enumerate(val):
                            joints[f"{base_name}_{i}"] = float(v)
                else:
                    joints[base_name] = float(val)

            bone_transforms: dict[str, dict[str, list[float]]] = {}
            for body_id in asset.subtree_body_ids:
                body_name = model.body(body_id).name
                bone_transforms[body_name] = {
                    "position": data.xpos[body_id].tolist(),
                    "orientation": data.xquat[body_id].tolist(),
                }

            if is_human_for_diag:
                # Dump per-body WORLD quats for the diagnostic joints. The
                # C++ world-quat driver consumes these directly; printing them
                # here makes it trivial to cross-check the UE
                # ``[DIAG WQUAT]`` log against the publisher.
                for diag_name in self.DIAG_JOINT_NAMES:
                    bt = bone_transforms.get(diag_name)
                    if not bt:
                        continue
                    bw, bx, by, bz = bt["orientation"]
                    diag_lines.append(
                        f"  {diag_name}: world_mujoco=("
                        f"{bw:+.3f},{bx:+.3f},{by:+.3f},{bz:+.3f}) "
                        f"-> world_ue=({bw:+.3f},{-bx:+.3f},{by:+.3f},{-bz:+.3f}) [done in C++]"
                    )

            if is_human_for_diag and diag_lines:
                print(
                    f"[mujoco_zmq_session DIAG seq={self._seq}] "
                    f"{asset_name} root_pos=({root_pos[0]:+.3f},"
                    f"{root_pos[1]:+.3f},{root_pos[2]:+.3f}) "
                    f"root_ori=({root_ori[0]:+.3f},{root_ori[1]:+.3f},"
                    f"{root_ori[2]:+.3f},{root_ori[3]:+.3f})\n"
                    + "\n".join(diag_lines),
                    flush=True,
                )

            frame_cls = HumanFrame if _is_human_asset(asset_name) else RobotFrame
            assets_data[asset_name] = frame_cls(
                root_position=root_pos,
                root_orientation=root_ori,
                joints=joints,
                bone_transforms=bone_transforms,
            ).to_dict()

        self.send_json({"seq": self._seq, "assets": assets_data})


def _is_human_asset(asset_name: str) -> bool:
    # Include "simpl" because our asset is named "simpl_neutral" (typo kept for back-compat).
    return any(keyword in asset_name.lower() for keyword in ("human", "smpl", "simpl", "person", "body"))
