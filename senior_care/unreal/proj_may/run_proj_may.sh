#!/usr/bin/env bash
# Launch the proj_may editor with the demo map preloaded.
#
# Use this AFTER you've already started run_test.py in another terminal
# (so the ZMQ publisher is up before the editor subsystem subscribes).
#
# Override UE_ROOT if your engine lives elsewhere.

set -euo pipefail

UE_ROOT="${UE_ROOT:-/home/heinrich/third_party/Linux_Unreal_Engine_5.6.1}"
PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="${PROJECT_DIR}/proj_may.uproject"

if [[ ! -x "${UE_ROOT}/Engine/Binaries/Linux/UnrealEditor" ]]; then
    echo "UnrealEditor not found at ${UE_ROOT}/Engine/Binaries/Linux/UnrealEditor" >&2
    echo "Set UE_ROOT to your UE 5.6 install root." >&2
    exit 1
fi

echo "Launching UE editor: ${PROJECT}"
exec "${UE_ROOT}/Engine/Binaries/Linux/UnrealEditor" "${PROJECT}"
