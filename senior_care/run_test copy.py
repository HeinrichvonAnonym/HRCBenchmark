from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

os_env = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(os_env))

from benchmark.senior_care.base.mujoco_script import (  # noqa: E402
    CMD_TOPIC_DEFAULT,
    STATE_TOPIC_DEFAULT,
    SeniorCareEnv,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "SeniorCare demo runner: Zenoh franka/command + franka/state and ZMQ UE are configured "
            "inside SeniorCareEnv by default."
        ),
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

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )

    config_path = Path(__file__).resolve().parent / "config" / "demo.yaml"
    env = SeniorCareEnv(
        config_path,
        zenoh_publish=args.zenoh_scene_publish,
        zenoh_franka_topics=not args.no_franka_wire,
        zenoh_cmd_topic=args.cmd_topic,
        zenoh_state_topic=args.state_topic,
        zenoh_connect_endpoints=args.connect if args.connect else None,
        zmq_publish=True,
        zmq_address=args.zmq_address,
        view_camera=args.view_camera,
        zmq_camera_address=args.zmq_camera_address,
    )
    env.reset()
    action = env.home_action()

    print(
        f"Zenoh (env): cmd={args.cmd_topic!r} state={args.state_topic!r}  "
        f"franka_topics={not args.no_franka_wire} "
        f"scene_publish={args.zenoh_scene_publish}  zmq={args.zmq_address!r}  "
        f"view_camera={args.view_camera}  camera_addr={args.zmq_camera_address!r}",
    )

    try:
        if args.render:
            import mujoco.viewer

            with mujoco.viewer.launch_passive(env.model, env.data) as viewer:
                n = 0
                while n < args.steps and viewer.is_running():
                    with viewer.lock():
                        env.step(action)
                    viewer.sync()
                    n += 1
        else:
            for _ in range(args.steps):
                env.step(action)
    finally:
        env.close()


if __name__ == "__main__":
    main()
