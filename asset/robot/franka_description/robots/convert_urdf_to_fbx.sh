#!/bin/bash

# URDF to FBX using URDF2FBX tool (via Blender)

BLENDER_BIN="/home/heinrich/blender-4.1.1-linux-x64/blender"
BLENDER_PYTHON="/home/heinrich/blender-4.1.1-linux-x64/4.1/python/bin/python3.11"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
URDF2FBX_DIR="$(cd "$SCRIPT_DIR/../../URDF2FBX" && pwd)"
OUTPUT_DIR="${SCRIPT_DIR}/fbx"
URDF_FILE="${SCRIPT_DIR}/franka_panda_gripper.urdf"

mkdir -p "$OUTPUT_DIR"

# 1. Install urdf_parser_py into Blender's Python if missing
"$BLENDER_PYTHON" -c "import urdf_parser_py" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing urdf_parser_py into Blender Python..."
    "$BLENDER_PYTHON" -m pip install urdf_parser_py
fi

# 2. Create a temp URDF with package:// paths resolved to absolute paths
FRANKA_DESC_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)/franka_description"
TEMP_URDF="${SCRIPT_DIR}/_tmp_franka.urdf"
sed "s|package://franka_description/|${FRANKA_DESC_DIR}/|g" "$URDF_FILE" > "$TEMP_URDF"

echo "Resolved package:// paths to: $FRANKA_DESC_DIR/"

# 3. Run URDF2FBX via Blender
FBX_OUT="${OUTPUT_DIR}/franka_panda_gripper.fbx"

WRAPPER_SCRIPT="${SCRIPT_DIR}/_tmp_wrapper.py"
cat > "$WRAPPER_SCRIPT" <<PYEOF
import sys
sys.path.insert(0, "${URDF2FBX_DIR}")

from urdf_importer.robot_builder import RobotBuilder
import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)

urdf_path = "${TEMP_URDF}"
fbx_path  = "${FBX_OUT}"

print(f"URDF: {urdf_path}")
print(f"FBX:  {fbx_path}")

RobotBuilder(urdf_path, False, False, False, False, True, 1.0)

# ---------------------------------------------------------------------------
# Post-process: convert bone-parenting to vertex-weight skinning
#
# URDF2FBX uses parent_set(type="BONE"), which creates a rigid bone-parent
# relationship with NO vertex weights. UE's skeletal mesh importer requires
# proper vertex weights to drive each mesh section independently.
#
# For each bone-parented mesh:
#   1. Add a vertex group named after its parent bone, weight 1.0 for all verts
#   2. Reparent the mesh to the armature object (not the individual bone)
#   3. Add an Armature modifier pointing to the armature
# ---------------------------------------------------------------------------

armature_obj = next(
    (obj for obj in bpy.data.objects if obj.type == "ARMATURE"), None
)

if armature_obj is None:
    print("[WARNING] No armature found, skipping skinning post-process.")
else:
    converted = 0
    for obj in list(bpy.data.objects):
        if obj.type != "MESH":
            continue
        if obj.parent != armature_obj:
            continue
        bone_name = obj.parent_bone
        if not bone_name:
            continue

        # 1. Add vertex group with 100% weight for all vertices
        if bone_name not in obj.vertex_groups:
            vg = obj.vertex_groups.new(name=bone_name)
        else:
            vg = obj.vertex_groups[bone_name]
        all_vert_indices = [v.index for v in obj.data.vertices]
        vg.add(all_vert_indices, 1.0, "REPLACE")

        # 2. Switch parent type from BONE to OBJECT so the mesh can use
        #    the Armature modifier (bone-parent + armature modifier is the
        #    correct UE-compatible skinning setup)
        obj.parent_type = "OBJECT"
        obj.parent_bone = ""

        # 3. Add Armature modifier if not already present
        if not any(m.type == "ARMATURE" for m in obj.modifiers):
            mod = obj.modifiers.new(name="Armature", type="ARMATURE")
            mod.object = armature_obj

        converted += 1
        print(f"  Skinned: {obj.name} → bone '{bone_name}'")

    print(f"[skinning] Converted {converted} mesh(es) to vertex-weight skinning.")

# Export with use_armature_deform_only=False so all bones are included,
# and bake_anim=False since we have no animation to bake.
bpy.ops.export_scene.fbx(
    filepath=fbx_path,
    object_types={"ARMATURE", "MESH"},
    mesh_smooth_type="FACE",
    add_leaf_bones=False,
    use_armature_deform_only=False,
    bake_anim=False,
)
print(f"Exported: {fbx_path}")
PYEOF

echo "=============================="
echo "Converting: franka_panda_gripper.urdf"
echo "=============================="
"$BLENDER_BIN" --background --python "$WRAPPER_SCRIPT"

# Cleanup temp files
rm -f "$TEMP_URDF" "$WRAPPER_SCRIPT"

echo ""
echo "Done. FBX saved to: $FBX_OUT"
