"""Tiny ZMQ publisher mimicking MuJoCo, for plugging-test purposes.

Run this from a terminal *outside* UE, then watch the UE Output Log: the
``SeniorCareBridge`` plugin should print ``[Bridge] frame seq=N ...``
lines. Once that works, switch back to the real MuJoCo runtime.

Usage::

    python -m benchmark.senior_care.tools.fake_mujoco_publisher \
        --address tcp://*:5556 --rate 30

Or directly::

    python /home/heinrich/roboLab/python/benchmark/senior_care/tools/fake_mujoco_publisher.py

The frame schema matches what ``MujocoZmqSession.publish_step`` emits:

    {
        "seq": int,
        "assets": {
            "<name>": {
                "root_position": [x, y, z],
                "root_orientation": [w, x, y, z],
                "joints": {"<joint>": float, ...},
                "bone_transforms": {}
            }
        }
    }
"""

from __future__ import annotations

import argparse
import json
import math
import time

import zmq


# Asset / joint defaults match config/demo.yaml so the C++ driver finds
# matching entries in its joint -> bone mapping out of the box.
DEFAULT_FRANKA_JOINTS: tuple[str, ...] = tuple(f"panda_joint{i}" for i in range(1, 8))
DEFAULT_HUMAN_JOINTS: tuple[str, ...] = ("r_elbow", "l_elbow", "r_knee", "l_knee")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--address", default="tcp://*:5556",
                        help="ZMQ PUB bind address (default: tcp://*:5556)")
    parser.add_argument("--rate", type=float, default=30.0,
                        help="Publish rate (Hz, default: 30)")
    parser.add_argument("--amp", type=float, default=0.8,
                        help="Joint sweep amplitude (rad, default: 0.8)")
    parser.add_argument("--period", type=float, default=4.0,
                        help="Joint sweep period (s, default: 4)")
    parser.add_argument("--franka-name", default="franka_emika_panda",
                        help="Asset name for the fake Franka (default: franka_emika_panda)")
    parser.add_argument("--human-name", default="simpl_neutral",
                        help="Asset name for the fake human (default: simpl_neutral)")
    return parser.parse_args()


def _build_frame(seq: int, t: float, args: argparse.Namespace) -> dict:
    omega = 2.0 * math.pi / max(1e-6, args.period)
    sweep = args.amp * math.sin(omega * t)

    franka_joints = {name: sweep for name in DEFAULT_FRANKA_JOINTS}
    human_joints = {name: sweep for name in DEFAULT_HUMAN_JOINTS}

    return {
        "seq": seq,
        "assets": {
            args.franka_name: {
                "root_position": [0.0, -0.2, 0.8],
                "root_orientation": [1.0, 0.0, 0.0, 0.0],
                "joints": franka_joints,
                "bone_transforms": {},
            },
            args.human_name: {
                "root_position": [0.65, 0.0, 0.75],
                "root_orientation": [1.0, 0.0, 0.0, 0.0],
                "joints": human_joints,
                "bone_transforms": {},
            },
        },
    }


def main() -> None:
    args = _parse_args()
    ctx = zmq.Context()
    socket = ctx.socket(zmq.PUB)
    socket.bind(args.address)

    # Slow joiners (UE just connected) miss the first few messages
    # without this -- the SUB side sets a 100ms timeout in the worker.
    print(f"[fake_publisher] bound to {args.address}; warming up...")
    time.sleep(0.5)

    period = 1.0 / max(1e-3, args.rate)
    seq = 0
    t0 = time.monotonic()
    try:
        while True:
            seq += 1
            now = time.monotonic() - t0
            payload = _build_frame(seq, now, args)
            socket.send(json.dumps(payload).encode())
            if seq % max(1, int(args.rate)) == 0:
                print(f"[fake_publisher] sent seq={seq} t={now:.2f}s sweep="
                      f"{payload['assets'][args.franka_name]['joints'][DEFAULT_FRANKA_JOINTS[0]]:+.3f}")
            time.sleep(period)
    except KeyboardInterrupt:
        print("[fake_publisher] stopping")
    finally:
        socket.close()
        ctx.term()


if __name__ == "__main__":
    main()
