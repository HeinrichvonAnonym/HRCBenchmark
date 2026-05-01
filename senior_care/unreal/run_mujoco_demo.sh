#!/usr/bin/env bash
# Setup and (optionally build &) launch the MuJoCo-UE5-Linux-plugin demo.
#
# Usage:
#   ./run_mujoco_demo.sh                 # setup only (move repo, create symlinks, generate project files)
#   ./run_mujoco_demo.sh --build         # also compile MujocoTestEditor (Linux Development)
#   ./run_mujoco_demo.sh --build --launch  # also open the editor at the end
#   ./run_mujoco_demo.sh --launch        # just launch (assumes already built)
#
# Env overrides:
#   UE_ROOT     path to Unreal Engine 5.6 (default: /home/heinrich/third_party/Linux_Unreal_Engine_5.6.1)
#   UNREAL_DIR  path containing the demo repo (default: this script's directory)

set -euo pipefail

UE_ROOT="${UE_ROOT:-/home/heinrich/third_party/Linux_Unreal_Engine_5.6.1}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UNREAL_DIR="${UNREAL_DIR:-$SCRIPT_DIR}"

DEMO_DIR_NAME="MuJoCo-UE5-Linux-plugin"
DEMO_DIR="$UNREAL_DIR/$DEMO_DIR_NAME"
UPROJECT="$DEMO_DIR/MujocoTest.uproject"

DO_BUILD=false
DO_LAUNCH=false

for arg in "$@"; do
    case "$arg" in
        --build)   DO_BUILD=true ;;
        --launch)  DO_LAUNCH=true ;;
        -h|--help)
            sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            exit 1
            ;;
    esac
done

log() { printf '\033[1;34m[demo]\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m[demo]\033[0m %s\n' "$*" >&2; }

# 1. Sanity-check Unreal Engine install
if [[ ! -x "$UE_ROOT/Engine/Binaries/Linux/UnrealEditor" ]]; then
    err "UnrealEditor not found at $UE_ROOT/Engine/Binaries/Linux/UnrealEditor"
    err "Set UE_ROOT to your UE 5.6 install."
    exit 1
fi
RUN_UBT="$UE_ROOT/Engine/Build/BatchFiles/RunUBT.sh"
if [[ ! -x "$RUN_UBT" ]]; then
    err "RunUBT.sh not found or not executable at $RUN_UBT"
    exit 1
fi

# 2. Move repo out of MyProject/Plugins if it's still nested there
LEGACY_PATH="$UNREAL_DIR/MyProject/Plugins/$DEMO_DIR_NAME"
if [[ -d "$LEGACY_PATH" && ! -e "$DEMO_DIR" ]]; then
    log "Moving $LEGACY_PATH -> $DEMO_DIR"
    mv "$LEGACY_PATH" "$DEMO_DIR"
elif [[ -d "$LEGACY_PATH" && -e "$DEMO_DIR" ]]; then
    err "Both $LEGACY_PATH and $DEMO_DIR exist. Please remove one and re-run."
    exit 1
fi

if [[ ! -f "$UPROJECT" ]]; then
    err "Demo uproject not found at $UPROJECT"
    exit 1
fi

# 3. Create the libmujoco.so symlinks the Build.cs expects
MJ_ROOT="$DEMO_DIR/Plugins/MuJoCoUE/Source/mujoco"
MJ_LIB="$MJ_ROOT/lib/libmujoco.so.3.3.0"
if [[ ! -f "$MJ_LIB" ]]; then
    err "Bundled MuJoCo library missing: $MJ_LIB"
    exit 1
fi
log "Ensuring libmujoco.so symlinks"
ln -sfn libmujoco.so.3.3.0       "$MJ_ROOT/lib/libmujoco.so"
ln -sfn ../lib/libmujoco.so.3.3.0 "$MJ_ROOT/bin/libmujoco.so"

# 4. Generate UE project files (idempotent; cheap; needed for IDE & first-time build)
log "Generating UE project files"
"$RUN_UBT" -ProjectFiles -Project="$UPROJECT" -Game

# 5. Optionally compile the editor target
if $DO_BUILD; then
    log "Building MujocoTestEditor (Linux Development) - first build can take 10-30 min"
    "$RUN_UBT" MujocoTestEditor Linux Development -Project="$UPROJECT"
else
    log "Skipping build (pass --build to compile MujocoTestEditor)."
fi

# 6. Optionally launch the editor
if $DO_LAUNCH; then
    log "Launching UnrealEditor with $UPROJECT"
    exec "$UE_ROOT/Engine/Binaries/Linux/UnrealEditor" "$UPROJECT"
else
    log "Done. To open the editor:"
    echo "    \"$UE_ROOT/Engine/Binaries/Linux/UnrealEditor\" \"$UPROJECT\""
fi
