"""In-editor entry point: load demo.yaml, optional test joint motion, stream cameras via ZMQ.

Run from the Unreal Editor::

    py "/path/to/benchmark/senior_care/test_ue.py"

See :class:`~benchmark.senior_care.ue_runner.UeEditorRunner` for behavior.
"""

from __future__ import annotations

import sys
from pathlib import Path

_THIS_DIR = Path(__file__).resolve().parent
_PYTHON_ROOT = _THIS_DIR.parents[1]

if str(_PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(_PYTHON_ROOT))

import unreal  # noqa: E402  # type: ignore[import-not-found]

from benchmark.senior_care.ue_runner import UeEditorRunner  # noqa: E402

CONFIG_PATH = _THIS_DIR / "config" / "demo.yaml"

APPLY_INITIAL_STATE = True
DRIVE_TEST_JOINTS = False
STREAM_CAMERAS = True
ZMQ_CAMERA_ADDRESS = "tcp://*:5557"
CAMERA_CAPTURE_HZ = 0.5

PANDA_JOINT1_AMPLITUDE_RAD = 1.0
PANDA_JOINT1_PERIOD_S = 4.0
HUMAN_FOREARM_AMPLITUDE_RAD = 0.8
HUMAN_FOREARM_PERIOD_S = 3.0


def main() -> None:
    runner = UeEditorRunner(
        config_path=CONFIG_PATH,
        apply_initial_state=APPLY_INITIAL_STATE,
        drive_test_joints=DRIVE_TEST_JOINTS,
        stream_cameras=STREAM_CAMERAS,
        zmq_camera_address=ZMQ_CAMERA_ADDRESS,
        camera_capture_hz=CAMERA_CAPTURE_HZ,
        python_parent=_PYTHON_ROOT,
        reload_senior_care_modules=True,
        panda_joint1_amplitude_rad=PANDA_JOINT1_AMPLITUDE_RAD,
        panda_joint1_period_s=PANDA_JOINT1_PERIOD_S,
        human_forearm_amplitude_rad=HUMAN_FOREARM_AMPLITUDE_RAD,
        human_forearm_period_s=HUMAN_FOREARM_PERIOD_S,
    )
    runner.start()


if __name__ == "__main__":
    main()
