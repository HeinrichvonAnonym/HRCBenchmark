from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmark.senior_care.base.mujoco_script import SeniorCareEnv


# Sine-wave drive parameters: panda_joint1 sweeps base yaw (most visible),
# panda_joint4 wiggles the elbow so the visual story isn't just one joint.
PANDA_JOINT1_AMPLITUDE_RAD = 0.8
PANDA_JOINT1_PERIOD_S = 4.0
PANDA_JOINT4_BIAS_RAD = -1.5
PANDA_JOINT4_AMPLITUDE_RAD = 0.5
PANDA_JOINT4_PERIOD_S = 5.0


def _drive_franka_actuators(action: dict, sim_time: float) -> None:
    """Overwrite panda_joint1/panda_joint4 targets with a slow sine wave."""
    panda = action["franka_emika_panda"]["position"]
    panda["panda_joint1"] = PANDA_JOINT1_AMPLITUDE_RAD * math.sin(
        2.0 * math.pi * sim_time / PANDA_JOINT1_PERIOD_S
    )
    panda["panda_joint4"] = PANDA_JOINT4_BIAS_RAD + PANDA_JOINT4_AMPLITUDE_RAD * math.sin(
        2.0 * math.pi * sim_time / PANDA_JOINT4_PERIOD_S
    )


def _drive_all_franka_joints(action: dict, sim_time: float) -> None:
    """Drive all 7 Franka joints with sine waves at staggered periods.

    Each joint uses a different period so they move independently, making
    it easy to visually diagnose which joint is broken in UE.
    """
    panda = action["franka_emika_panda"]["position"]
    for i in range(1, 8):
        amplitude = 0.4  # radians – safe for all joints
        period = 3.0 + i * 0.5  # 3.5 s, 4.0 s, … 6.5 s
        panda[f"panda_joint{i}"] = amplitude * math.sin(
            2.0 * math.pi * sim_time / period
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--render", action="store_true", help="launch MuJoCo viewer")
    parser.add_argument("--steps", type=int, default=20000, help="number of simulation steps")
    parser.add_argument(
        "--all-joints",
        action="store_true",
        help="drive all 7 Franka joints with sine waves (diagnostic mode)",
    )
    args = parser.parse_args()

    drive_fn = _drive_all_franka_joints if args.all_joints else _drive_franka_actuators

    config_path = Path(__file__).resolve().parent / "config" / "demo.yaml"
    env = SeniorCareEnv(config_path, zmq_publish=True)

    observation = env.reset()
    action = env.home_action()

    if args.render:
        import mujoco.viewer

        with mujoco.viewer.launch_passive(env.model, env.data) as viewer:
            for step_id in range(args.steps):
                if not viewer.is_running():
                    break
                drive_fn(action, step_id * env.dt)
                observation = env.step(action)
                viewer.sync()
                time.sleep(env.dt)
                if step_id % 500 == 0:
                    print(
                        f"step={step_id} "
                        f"panda_joint1={observation['franka_emika_panda']['position']['panda_joint1']:.4f} "
                        f"panda_joint4={observation['franka_emika_panda']['position']['panda_joint4']:.4f} "
                        f"human_root_z={observation['simpl_neutral']['root_position'][2]:.4f}"
                    )
    else:
        for step_id in range(args.steps):
            drive_fn(action, step_id * env.dt)
            observation = env.step(action)
            if step_id % 500 == 0:
                print(
                    f"step={step_id} "
                    f"panda_joint1={observation['franka_emika_panda']['position']['panda_joint1']:.4f} "
                    f"panda_joint4={observation['franka_emika_panda']['position']['panda_joint4']:.4f} "
                    f"human_root_z={observation['simpl_neutral']['root_position'][2]:.4f}"
                )

    print("final observation:")
    print(observation)


if __name__ == "__main__":
    main()
