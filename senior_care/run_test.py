from __future__ import annotations

import argparse
import sys
from pathlib import Path

os_env = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(os_env))

from benchmark.senior_care.base.mujoco_script import (  # noqa: E402
    CMD_TOPIC_DEFAULT,
    STATE_TOPIC_DEFAULT,
)
from benchmark.senior_care.mujoco_runner import (  # noqa: E402
    MujocoRunner,
    MujocoRunnerConfig,
)


def main() -> None:
    _default_config = Path(__file__).resolve().parent / "config" / "demo.yaml"
    parser = argparse.ArgumentParser(
        description=(
            "SeniorCare demo runner: Zenoh franka/command + franka/state and ZMQ UE are configured "
            "inside SeniorCareEnv by default."
        ),
    )
    parser.add_argument(
        "--config",
        dest="config_path",
        type=Path,
        default=_default_config,
        help=f"YAML config for SeniorCareEnv (default: {_default_config})",
    )
    parser.add_argument("--render", action="store_true", help="MuJoCo viewer")
    parser.add_argument("--steps", type=int, default=2_000_000, help="max steps")
    parser.add_argument("--cmd-topic", default=CMD_TOPIC_DEFAULT, help="Zenoh subscribe key")
    parser.add_argument(
        "--state-topic",
        default=STATE_TOPIC_DEFAULT,
        help="Zenoh RobotObservation publish key",
    )
    parser.add_argument(
        "--zmq-address",
        default="tcp://localhost:5556",
        help="ZMQ PUB bind/connect address for UE bridge",
    )
    parser.add_argument(
        "--view-camera", "--view_camera",
        dest="view_camera",
        action="store_true",
        help=(
            "Subscribe to virtual camera RGBD frames from UE and display them "
            "via OpenCV (requires opencv-python). Implies --zmq-publish."
        ),
    )
    parser.add_argument(
        "--zmq-camera-address", "--zmq_camera_address",
        dest="zmq_camera_address",
        default="tcp://localhost:5557",
        help=(
            "ZMQ SUB connect address for RGBD camera frames published by UE "
            "(default: tcp://localhost:5557)"
        ),
    )
    parser.add_argument(
        "--no-franka-wire",
        action="store_true",
        help="disable Zenoh subscribe franka/command + publish franka/state (SeniorCareEnv)",
    )
    parser.add_argument(
        "--zenoh-scene-publish",
        action="store_true",
        help=(
            "enable legacy HumanState Zenoh (and mujoco echoes on franka/* only when franka-wire is OFF)"
        ),
    )
    parser.add_argument(
        "-e",
        "--connect",
        action="append",
        default=None,
        metavar="ENDPOINT",
        help="Zenoh connect endpoints, e.g. tcp/127.0.0.1:7447 (repeat)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="root logging level (SeniorCareEnv logs franka/command at INFO)",
    )
    args = parser.parse_args()

    config = MujocoRunnerConfig.from_argparse(args)
    MujocoRunner(config).start()


if __name__ == "__main__":
    main()
