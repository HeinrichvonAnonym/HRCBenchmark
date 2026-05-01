#!/bin/bash

# SMPLX PKL to OBJ/FBX Converter
# This script converts SMPLX pkl files to OBJ and FBX formats using Blender

BLENDER_ROOT="/home/heinrich/blender-4.1.1-linux-x64"
BLENDER_BIN="${BLENDER_ROOT}/blender"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_OBJ_DIR="${SCRIPT_DIR}/obj"
OUTPUT_FBX_DIR="${SCRIPT_DIR}/fbx"

# Check if Blender exists
if [ ! -f "$BLENDER_BIN" ]; then
    echo "Error: Blender not found at $BLENDER_BIN"
    exit 1
fi

# Create output directories if they don't exist
mkdir -p "$OUTPUT_OBJ_DIR"
mkdir -p "$OUTPUT_FBX_DIR"

# Create temporary Python script for Blender
BLENDER_SCRIPT=$(cat <<'EOF'
import bpy
import pickle
import numpy as np
import sys
import os
from mathutils import Vector, Matrix

# SMPLX joint names (54 joints total)
SMPLX_JOINT_NAMES = [
    'pelvis', 'left_hip', 'right_hip', 'spine1', 'left_knee', 'right_knee', 'spine2', 'left_ankle', 'right_ankle',
    'spine3', 'left_foot', 'right_foot', 'neck', 'left_collar', 'right_collar', 'head', 'left_shoulder', 'right_shoulder',
    'left_elbow', 'right_elbow', 'left_wrist', 'right_wrist', 'jaw', 'left_eye_smplhf', 'right_eye_smplhf',
    'left_index1', 'left_index2', 'left_index3', 'left_middle1', 'left_middle2', 'left_middle3', 'left_pinky1',
    'left_pinky2', 'left_pinky3', 'left_ring1', 'left_ring2', 'left_ring3', 'left_thumb1', 'left_thumb2', 'left_thumb3',
    'right_index1', 'right_index2', 'right_index3', 'right_middle1', 'right_middle2', 'right_middle3', 'right_pinky1',
    'right_pinky2', 'right_pinky3', 'right_ring1', 'right_ring2', 'right_ring3', 'right_thumb1', 'right_thumb2', 'right_thumb3'
]

def load_smplx_model(pkl_path):
    """Load SMPLX model from pickle file"""
    with open(pkl_path, 'rb') as f:
        model_data = pickle.load(f, encoding='latin1')
    return model_data

def create_armature_from_smplx(model_data, name="SMPLX_Armature"):
    """Create Blender armature from SMPLX skeleton"""
    # Get joint positions and kinematic tree
    if 'J_regressor' in model_data:
        J_regressor = np.array(model_data['J_regressor'].todense()) if hasattr(model_data['J_regressor'], 'todense') else np.array(model_data['J_regressor'])
        v_template = np.array(model_data.get('v_template', model_data.get('V_template')))
        joint_positions = np.dot(J_regressor, v_template)
    else:
        print("Warning: No J_regressor found, using default joint positions if available")
        joint_positions = None
    
    kintree = model_data.get('kintree_table', None)
    if kintree is None:
        print("Warning: No kinematic tree found")
        return None
    
    kintree = np.array(kintree)
    
    # Create armature object
    armature = bpy.data.armatures.new(name)
    armature_obj = bpy.data.objects.new(name, armature)
    bpy.context.collection.objects.link(armature_obj)
    bpy.context.view_layer.objects.active = armature_obj
    armature_obj.select_set(True)
    
    # Enter edit mode to create bones
    bpy.ops.object.mode_set(mode='EDIT')
    
    # Create bones
    bones = {}
    num_joints = min(len(SMPLX_JOINT_NAMES), kintree.shape[1]) if joint_positions is not None else kintree.shape[1]
    
    for i in range(num_joints):
        bone_name = SMPLX_JOINT_NAMES[i] if i < len(SMPLX_JOINT_NAMES) else f"joint_{i}"
        bone = armature.edit_bones.new(bone_name)
        
        if joint_positions is not None:
            pos = joint_positions[i]
            bone.head = Vector((pos[0], pos[1], pos[2]))
            # Tail is offset slightly for now, will be adjusted based on children
            bone.tail = Vector((pos[0], pos[1] + 0.1, pos[2]))
        else:
            bone.head = Vector((0, i * 0.1, 0))
            bone.tail = Vector((0, i * 0.1 + 0.1, 0))
        
        bones[i] = bone
    
    # Set up parent-child relationships
    for i in range(num_joints):
        parent_idx = kintree[0, i]
        if parent_idx >= 0 and parent_idx < num_joints:
            bones[i].parent = bones[parent_idx]
            # Adjust tail of parent to point towards child
            if joint_positions is not None:
                direction = bones[i].head - bones[parent_idx].head
                if direction.length > 0.001:
                    bones[parent_idx].tail = bones[parent_idx].head + direction * 0.5
    
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return armature_obj

def create_mesh_from_smplx(model_data, armature_obj, name="SMPLX"):
    """Create a Blender mesh from SMPLX model data and bind to armature"""
    # Get vertices and faces
    if 'v_template' in model_data:
        vertices = model_data['v_template']
    elif 'V_template' in model_data:
        vertices = model_data['V_template']
    else:
        print("Error: Could not find vertices in model data")
        print("Available keys:", model_data.keys())
        return None
    
    if 'f' in model_data:
        faces = model_data['f']
    elif 'faces' in model_data:
        faces = model_data['faces']
    else:
        print("Error: Could not find faces in model data")
        return None
    
    # Get skinning weights
    weights = model_data.get('weights', None)
    
    # Convert to appropriate format
    vertices = np.array(vertices)
    faces = np.array(faces)
    if weights is not None:
        weights = np.array(weights)
    
    # Create mesh
    mesh = bpy.data.meshes.new(name)
    mesh_obj = bpy.data.objects.new(name, mesh)
    
    # Link to scene
    bpy.context.collection.objects.link(mesh_obj)
    bpy.context.view_layer.objects.active = mesh_obj
    mesh_obj.select_set(True)
    
    # Create mesh from vertices and faces
    mesh.from_pydata(vertices.tolist(), [], faces.tolist())
    mesh.update()
    
    # Add armature modifier if armature exists
    if armature_obj is not None:
        # Parent mesh to armature
        mesh_obj.parent = armature_obj
        
        # Add armature modifier
        mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
        mod.object = armature_obj
        
        # Create vertex groups and assign weights
        if weights is not None:
            num_joints = min(weights.shape[1], len(SMPLX_JOINT_NAMES))
            for i in range(num_joints):
                bone_name = SMPLX_JOINT_NAMES[i] if i < len(SMPLX_JOINT_NAMES) else f"joint_{i}"
                vg = mesh_obj.vertex_groups.new(name=bone_name)
                
                # Assign weights for each vertex
                for v_idx in range(len(vertices)):
                    weight = weights[v_idx, i]
                    if weight > 0.001:  # Only assign non-zero weights
                        vg.add([v_idx], weight, 'REPLACE')
            
            print(f"Applied skinning weights: {num_joints} joints, {len(vertices)} vertices")
    
    return mesh_obj

def convert_pkl_to_formats(pkl_path, obj_path, fbx_path):
    """Convert SMPLX pkl file to OBJ and FBX formats with skeleton"""
    print(f"Converting: {pkl_path}")
    
    # Clear existing mesh objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    # Load SMPLX model
    try:
        model_data = load_smplx_model(pkl_path)
        print(f"Loaded model with keys: {list(model_data.keys())}")
    except Exception as e:
        print(f"Error loading pkl file: {e}")
        return False
    
    model_name = os.path.splitext(os.path.basename(pkl_path))[0]
    
    # Create armature (skeleton)
    print("Creating armature...")
    armature_obj = create_armature_from_smplx(model_data, f"{model_name}_Armature")
    
    if armature_obj is None:
        print("Warning: Failed to create armature, proceeding with mesh only")
    else:
        print(f"Created armature with {len(armature_obj.data.bones)} bones")
    
    # Create mesh and bind to armature
    print("Creating mesh...")
    mesh_obj = create_mesh_from_smplx(model_data, armature_obj, model_name)
    
    if mesh_obj is None:
        print(f"Failed to create mesh from {pkl_path}")
        return False
    
    print(f"Created mesh with {len(mesh_obj.data.vertices)} vertices and {len(mesh_obj.data.polygons)} faces")
    
    # Select both armature and mesh for export
    bpy.ops.object.select_all(action='DESELECT')
    if armature_obj:
        armature_obj.select_set(True)
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = armature_obj if armature_obj else mesh_obj
    
    # Export to OBJ (OBJ format doesn't support skeletons well, so just export mesh)
    try:
        mesh_obj.select_set(True)
        if armature_obj:
            armature_obj.select_set(False)
        bpy.ops.wm.obj_export(
            filepath=obj_path,
            export_selected_objects=True,
            export_materials=False,
            export_triangulated_mesh=True
        )
        print(f"Exported OBJ (mesh only): {obj_path}")
    except Exception as e:
        print(f"Error exporting OBJ: {e}")
        return False
    
    # Export to FBX (includes skeleton and skinning)
    try:
        bpy.ops.object.select_all(action='DESELECT')
        if armature_obj:
            armature_obj.select_set(True)
        mesh_obj.select_set(True)
        
        bpy.ops.export_scene.fbx(
            filepath=fbx_path,
            use_selection=True,
            use_armature_deform_only=True,
            add_leaf_bones=False,
            bake_anim=False,
            mesh_smooth_type='FACE',
            apply_scale_options='FBX_SCALE_ALL'
        )
        print(f"Exported FBX (mesh + skeleton + skinning): {fbx_path}")
    except Exception as e:
        print(f"Error exporting FBX: {e}")
        return False
    
    return True

# Main execution
if __name__ == "__main__":
    # Get arguments passed from bash script
    if len(sys.argv) < 7:
        print("Usage: blender --background --python script.py -- <pkl_path> <obj_path> <fbx_path>")
        sys.exit(1)
    
    # Arguments after '--' are in sys.argv after the '--'
    args = sys.argv[sys.argv.index('--') + 1:]
    pkl_path = args[0]
    obj_path = args[1]
    fbx_path = args[2]
    
    success = convert_pkl_to_formats(pkl_path, obj_path, fbx_path)
    
    if success:
        print("Conversion successful!")
        sys.exit(0)
    else:
        print("Conversion failed!")
        sys.exit(1)
EOF
)

# Save Python script to temporary file
TEMP_SCRIPT="${SCRIPT_DIR}/convert_smplx_temp.py"
echo "$BLENDER_SCRIPT" > "$TEMP_SCRIPT"

# Process each pkl file
for pkl_file in "${SCRIPT_DIR}"/SMPLX_*.pkl; do
    if [ -f "$pkl_file" ]; then
        filename=$(basename "$pkl_file" .pkl)
        obj_output="${OUTPUT_OBJ_DIR}/${filename}.obj"
        fbx_output="${OUTPUT_FBX_DIR}/${filename}.fbx"
        
        echo "================================================"
        echo "Processing: $filename"
        echo "================================================"
        
        # Run Blender in background mode
        "$BLENDER_BIN" --background --python "$TEMP_SCRIPT" -- "$pkl_file" "$obj_output" "$fbx_output"
        
        if [ $? -eq 0 ]; then
            echo "✓ Successfully converted $filename"
        else
            echo "✗ Failed to convert $filename"
        fi
        echo ""
    fi
done

# Clean up temporary script
rm -f "$TEMP_SCRIPT"

echo "================================================"
echo "Conversion complete!"
echo "OBJ files saved to: $OUTPUT_OBJ_DIR"
echo "FBX files saved to: $OUTPUT_FBX_DIR"
echo "================================================"
