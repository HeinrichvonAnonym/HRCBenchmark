#!/usr/bin/env bash
# Full MuJoCo demo: viewer + ZMQ UE bridge + Zenoh franka wire + scene publish + camera SUB/OpenCV.
#
# Non-interactive shells do not run conda init hooks; initialize conda explicitly before activate.
# Override env name: CONDA_ENV=myenv bash run_mujoco_full_demo.sh
# Skip conda: NO_CONDA=1 bash run_mujoco_full_demo.sh
set -euo pipefail

CONDA_ENV="${CONDA_ENV:-roboLab}"

if [[ "${NO_CONDA:-0}" != "1" ]]; then
  if ! command -v conda >/dev/null 2>&1; then
    echo "run_mujoco_full_demo.sh: conda not found on PATH." >&2
    exit 1
  fi
  eval "$(conda shell.bash hook)"
  conda activate "${CONDA_ENV}"
fi

_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}$(cd "${_SCRIPT_DIR}/../.." && pwd)"
exec python "${_SCRIPT_DIR}/run_test.py" \
  --render \
  --view-camera \
  --zenoh-scene-publish \
  "$@"
