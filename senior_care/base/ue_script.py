"""Editor-side runtime for the UE simulation -- thin setup layer.

Real-time bone driving lives in the C++ ``SeniorCareBridge`` plugin
(``AMuJoCoSkeletalActor`` + ``UMuJoCoBridgeSubsystem``). This module's
job has shrunk to a one-shot setup pass:

1. :class:`UeAssetLoader` -- imports each FBX listed in the YAML as a
   ``SkeletalMesh`` (idempotent; reuses existing imports).
2. :meth:`UeAssetLoader.spawn_actor` -- spawns an
   ``AMuJoCoSkeletalActor`` (the C++ class shipped by the plugin),
   assigns the SkeletalMesh via the exposed ``set_skinned_asset``
   UFUNCTION, and configures the routing key + joint -> bone mapping
   so the C++ subsystem can drive bones from MuJoCo's ZMQ frames.
3. :class:`UeJointDriver` -- kept as a *deprecated* wrapper so older
   callers keep importing. ``set_joint_angle`` / ``apply_initial_state``
   are now no-ops (the C++ driver owns this); ``set_root_pose`` still
   works because it just moves the actor's root transform.

The companion module :mod:`benchmark.senior_care.base.scene.ue_scene`
contains the YAML-parsing logic and the joint-name -> bone-name
aliases (kept ``unreal``-free so it stays unit-testable).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import unreal  # type: ignore[import-not-found]

from benchmark.senior_care.base.scene.ue_scene import (
    UeAssetSpec,
    UeCameraSpec,
    UeScene,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CONTENT_ROOT = "/Game/SeniorCare/Imported"
RIG_ROOT = "/Game/SeniorCare/RuntimeRigs"  # kept for back-compat exports

# Default rotation axis for joints whose YAML doesn't specify one.
# URDF2FBX (robot_builder.py) sets each bone's head→tail direction (= Blender
# bone local-Y) to the URDF joint rotation axis in world space.  After
# Blender→FBX→UE import the correct BoneSpace formula is therefore
# InitialRot * R(θ, Y_local), so we use "y" here.
_DEFAULT_JOINT_AXIS = "y"


# ---------------------------------------------------------------------------
# Quaternion helper (we deliberately avoid numpy here)
# ---------------------------------------------------------------------------


def _quat_wxyz_to_unreal_rotator(quat_wxyz: tuple[float, float, float, float]) -> unreal.Rotator:
    """Convert a (w, x, y, z) unit quaternion to an ``unreal.Rotator``.

    UE's coordinate system is left-handed (X forward, Y right, Z up). The
    quaternions in our YAMLs come from MuJoCo (right-handed, X forward,
    Y left, Z up) so we mirror Y to match. This only matters when the
    orientation is non-trivial; for the Franka in the demo the quaternion
    is a 180 deg rotation about X which is unaffected by the mirror.
    """
    w, x, y, z = quat_wxyz
    norm = math.sqrt(w * w + x * x + y * y + z * z) or 1.0
    w, x, y, z = w / norm, x / norm, y / norm, z / norm
    y = -y  # handedness flip
    quat = unreal.Quat(x, y, z, w)
    return quat.rotator()


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


@dataclass
class _LoadedAsset:
    """Bookkeeping for a successfully spawned asset."""

    spec: UeAssetSpec
    skeletal_mesh: Any  # unreal.SkeletalMesh
    skeleton: Any       # unreal.Skeleton
    actor: Any          # unreal.MuJoCoSkeletalActor
    skeleton_bone_names: list[str] = field(default_factory=list)
    bone_to_control_name: dict[str, str] = field(default_factory=dict)


class UeAssetLoader:
    """Imports FBXs and spawns ``AMuJoCoSkeletalActor`` instances.

    All operations are idempotent: re-running the script after a successful
    load will reuse existing imported uassets.
    """

    def __init__(self) -> None:
        self._asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        self._editor_asset_lib = unreal.EditorAssetLibrary
        self._actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # -- Scene cleanup ------------------------------------------------------

    def clear_scene_actors(
        self,
        *,
        label_prefix: str = "SeniorCare_",
        also_delete_classes: tuple[type, ...] = (),
    ) -> int:
        """Delete previously spawned scene actors. Returns the number deleted.

        By default we only delete actors whose label starts with
        ``label_prefix`` (i.e. actors this loader created in earlier runs),
        so this is safe to call on hand-authored levels.

        ``also_delete_classes`` lets callers widen the net to whole UClasses
        (e.g. ``(unreal.SkeletalMeshActor,)`` to nuke every skeletal mesh
        actor regardless of label).
        """
        all_actors = list(self._actor_subsystem.get_all_level_actors())
        to_delete: list[Any] = []
        for actor in all_actors:
            if actor is None:
                continue
            try:
                label = actor.get_actor_label()
            except Exception:
                label = ""
            if label.startswith(label_prefix):
                to_delete.append(actor)
                continue
            if also_delete_classes and isinstance(actor, also_delete_classes):
                to_delete.append(actor)

        deleted = 0
        for actor in to_delete:
            try:
                self._actor_subsystem.destroy_actor(actor)
                deleted += 1
            except Exception as exc:
                unreal.log_warning(
                    f"[UeAssetLoader] could not destroy actor "
                    f"'{actor.get_actor_label()}': {exc}"
                )

        unreal.log(
            f"[UeAssetLoader] clear_scene_actors: deleted {deleted} actor(s) "
            f"(prefix='{label_prefix}', extra_classes={[c.__name__ for c in also_delete_classes]})"
        )
        return deleted

    # -- FBX import ---------------------------------------------------------

    def import_skeletal_mesh(self, spec: UeAssetSpec) -> tuple[Any, Any]:
        """Import the FBX referenced by ``spec`` and return ``(mesh, skeleton)``."""
        dest_dir = f"{CONTENT_ROOT}/{spec.name}"
        ue_model_path = spec.ue_model_path
        asset_basename = ue_model_path.stem
        expected_mesh_path = f"{dest_dir}/{asset_basename}"

        existing = self._try_load_existing_skeletal_mesh(dest_dir)
        if existing is not None:
            mesh, skeleton = existing
            unreal.log(f"[UeAssetLoader] reusing existing SkeletalMesh: {mesh.get_path_name()}")
            return mesh, skeleton

        if not ue_model_path.exists():
            raise FileNotFoundError(
                f"Asset '{spec.name}' refers to ue_model='{ue_model_path}' which does not exist."
            )

        fbx_options = unreal.FbxImportUI()
        fbx_options.set_editor_property("import_mesh", True)
        fbx_options.set_editor_property("import_animations", False)
        fbx_options.set_editor_property("import_materials", True)
        fbx_options.set_editor_property("import_textures", True)
        fbx_options.set_editor_property("create_physics_asset", True)
        fbx_options.set_editor_property("automated_import_should_detect_type", False)
        fbx_options.set_editor_property("original_import_type", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
        fbx_options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
        fbx_options.set_editor_property("import_uniform_scale", 100.0)

        sk_data = fbx_options.skeletal_mesh_import_data
        sk_data.set_editor_property("import_morph_targets", True)
        sk_data.set_editor_property("use_t0_as_ref_pose", True)
        sk_data.set_editor_property("preserve_smoothing_groups", True)
        sk_data.set_editor_property("update_skeleton_reference_pose", False)

        task = unreal.AssetImportTask()
        task.set_editor_property("filename", str(ue_model_path))
        task.set_editor_property("destination_path", dest_dir)
        task.set_editor_property("destination_name", asset_basename)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("save", True)
        task.set_editor_property("options", fbx_options)

        unreal.log(f"[UeAssetLoader] importing FBX '{ue_model_path}' -> {dest_dir}")
        self._asset_tools.import_asset_tasks([task])

        mesh = self._editor_asset_lib.load_asset(expected_mesh_path)
        if not isinstance(mesh, unreal.SkeletalMesh):
            mesh = self._scan_directory_for_skeletal_mesh(dest_dir)
        if mesh is None:
            raise RuntimeError(
                f"FBX import for '{spec.name}' did not produce a SkeletalMesh under {dest_dir}."
            )

        skeleton = mesh.skeleton
        if skeleton is None:
            raise RuntimeError(
                f"Imported SkeletalMesh '{mesh.get_path_name()}' has no Skeleton attached."
            )
        return mesh, skeleton

    def _try_load_existing_skeletal_mesh(self, dest_dir: str) -> tuple[Any, Any] | None:
        if not self._editor_asset_lib.does_directory_exist(dest_dir):
            return None
        mesh = self._scan_directory_for_skeletal_mesh(dest_dir)
        if mesh is None:
            return None
        skeleton = mesh.skeleton
        if skeleton is None:
            return None
        return mesh, skeleton

    def _scan_directory_for_skeletal_mesh(self, dest_dir: str) -> Any | None:
        for asset_path in self._editor_asset_lib.list_assets(dest_dir, recursive=True, include_folder=False):
            asset = self._editor_asset_lib.load_asset(asset_path)
            if isinstance(asset, unreal.SkeletalMesh):
                return asset
        return None

    # -- Spawning -----------------------------------------------------------

    def spawn_actor(
        self,
        spec: UeAssetSpec,
        skeletal_mesh: Any,
        skeleton: Any,
    ) -> _LoadedAsset:
        """Spawn an ``AMuJoCoSkeletalActor`` and configure it for MuJoCo driving.

        Returns a :class:`_LoadedAsset` capturing the spawned actor plus
        the bone-name introspection used to build the joint -> bone JSON
        the C++ driver consumes. Real-time joint driving happens in the
        plugin's tick (``UMuJoCoDrivenSkeletonComponent``); this Python
        side only does setup.
        """
        actor_class = self._get_mujoco_actor_class()

        location = unreal.Vector(*spec.root_position_cm)
        rotation = _quat_wxyz_to_unreal_rotator(spec.root_rotation_wxyz)

        actor = self._actor_subsystem.spawn_actor_from_class(
            actor_class, location, rotation
        )
        if actor is None:
            raise RuntimeError(f"Failed to spawn AMuJoCoSkeletalActor for '{spec.name}'.")

        actor.set_actor_label(f"SeniorCare_{spec.name}")

        scale = float(spec.scale or 1.0)
        actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))

        root_component = actor.root_component
        if root_component is not None:
            try:
                root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
            except Exception as exc:
                unreal.log_warning(
                    f"[UeAssetLoader] could not set mobility on '{spec.name}': {exc}"
                )

        # Hand off the SkeletalMesh to the C++ side. ``set_skinned_asset``
        # is the BlueprintCallable UFUNCTION that internally calls
        # ``UPoseableMeshComponent::SetSkinnedAssetAndUpdate``. We use the
        # C++ entry-point because the Python binding for the same
        # underlying call has historically been flaky on UE 5.1.
        try:
            actor.set_skinned_asset(skeletal_mesh)
        except Exception as exc:
            raise RuntimeError(
                f"actor.set_skinned_asset failed for '{spec.name}': {exc}"
            ) from exc

        # Routing key + joint -> bone mapping.
        try:
            actor.set_asset_name(spec.name)
        except Exception as exc:
            unreal.log_warning(
                f"[UeAssetLoader] set_asset_name failed for '{spec.name}': {exc}"
            )

        skeleton_bones = self._bone_names_from_actor(actor)
        if not skeleton_bones:
            skeleton_bones = self._enumerate_bone_names(skeletal_mesh)
        if not skeleton_bones:
            unreal.log_warning(
                f"[UeAssetLoader] '{spec.name}': could NOT enumerate bone "
                f"names (PoseableMesh + SkeletalMesh fallbacks both empty). "
                f"joint->bone mapping will be empty."
            )
        bone_to_control = self._fuzzy_match_bones(spec.drivable_bones, skeleton_bones)

        joint_to_bone = self._build_joint_to_bone_mapping(spec, bone_to_control)
        if not joint_to_bone:
            unreal.log_warning(
                f"[UeAssetLoader] '{spec.name}': joint_to_bone is EMPTY. "
                f"drivable_bones={list(spec.drivable_bones)[:6]}... "
                f"bone_to_control={dict(list(bone_to_control.items())[:4])}... "
                f"joint_order={list(getattr(spec, 'joint_order', None) or spec.selected_joints)[:6]}..."
            )
        try:
            mapping_json = json.dumps({"joint_to_bone": joint_to_bone})
            unreal.log(
                f"[UeAssetLoader] '{spec.name}' calling "
                f"set_bone_name_mapping_json (json_len={len(mapping_json)}, "
                f"entries={len(joint_to_bone)})"
            )
            actor.set_bone_name_mapping_json(mapping_json)
        except Exception as exc:
            unreal.log_warning(
                f"[UeAssetLoader] set_bone_name_mapping_json failed for "
                f"'{spec.name}': {exc}"
            )

        # Force-enable editor tick for the driver component. Setting
        # bTickInEditor=true in the C++ ctor isn't always honoured for
        # actors spawned via EditorActorSubsystem on UE 5.1; explicitly
        # toggling it here makes the driver's TickComponent fire reliably.
        try:
            driver = actor.get_driver() if hasattr(actor, "get_driver") else None
            if driver is not None:
                if hasattr(driver, "set_component_tick_enabled"):
                    driver.set_component_tick_enabled(True)
                if hasattr(driver, "activate"):
                    driver.activate(True)
                # Set fix_base so driver knows whether to update root transform.
                if hasattr(driver, "set_fix_base"):
                    driver.set_fix_base(spec.fix_base)
                    unreal.log(
                        f"[UeAssetLoader] '{spec.name}' set_fix_base({spec.fix_base})"
                    )
                unreal.log(
                    f"[UeAssetLoader] '{spec.name}' driver tick enabled "
                    f"(is_active={getattr(driver, 'is_active', lambda: '?')() if hasattr(driver, 'is_active') else '?'})"
                )
            else:
                unreal.log_warning(
                    f"[UeAssetLoader] '{spec.name}': actor.get_driver() returned None"
                )
        except Exception as exc:
            unreal.log_warning(
                f"[UeAssetLoader] '{spec.name}': could not enable driver tick: {exc}"
            )

        try:
            actor.set_actor_tick_enabled(True)
        except Exception:
            pass

        if not spec.use_imported_materials:
            self._apply_material_overrides(actor, spec)

        unreal.log(
            f"[UeAssetLoader] spawned '{spec.name}' at "
            f"({location.x:.2f}, {location.y:.2f}, {location.z:.2f}) "
            f"(scale={scale}, fix_base={spec.fix_base}, "
            f"bones={len(skeleton_bones)}, mapped={len(bone_to_control)}, "
            f"joint_to_bone={len(joint_to_bone)})"
        )

        return _LoadedAsset(
            spec=spec,
            skeletal_mesh=skeletal_mesh,
            skeleton=skeleton,
            actor=actor,
            skeleton_bone_names=skeleton_bones,
            bone_to_control_name=bone_to_control,
        )

    # -- Camera spawning ----------------------------------------------------

    def spawn_cameras(
        self,
        camera_specs: list[UeCameraSpec],
    ) -> list[dict]:
        """Spawn a ``CineCameraActor`` + two ``SceneCaptureComponent2D``
        components (RGB and depth) for each camera described in ``camera_specs``.

        Parameters
        ----------
        camera_specs : Parsed from the ``cameras:`` block of demo.yaml via
            :class:`~scene.ue_scene.UeScene`.

        Returns
        -------
        list of dict
            One dict per camera with keys:
            ``spec, actor, rt_rgb, rt_depth, cap_rgb, cap_depth``.
            Pass this list to :func:`_build_tick_callback` in ``test_ue.py``
            so the editor tick can capture + stream frames.
        """
        world = unreal.EditorLevelLibrary.get_editor_world()
        spawned: list[dict] = []

        for spec in camera_specs:
            loc = unreal.Vector(*spec.position_cm)
            rot = _quat_wxyz_to_unreal_rotator(spec.orientation_wxyz)

            # Spawn a plain CameraActor (no physical-camera exposure
            # simulation, so the preview widget just works).
            camera_actor = self._actor_subsystem.spawn_actor_from_class(
                unreal.CameraActor, loc, rot
            )
            if camera_actor is None:
                unreal.log_warning(
                    f"[UeAssetLoader] spawn_cameras: failed to spawn CameraActor "
                    f"for '{spec.name}'"
                )
                continue
            camera_actor.set_actor_label(f"SeniorCare_Camera_{spec.name}")

            # Set FOV on the embedded CameraComponent.
            try:
                cam_comps = camera_actor.get_components_by_class(
                    unreal.CameraComponent
                )
                if cam_comps:
                    cam_comp = cam_comps[0]
                    cam_comp.set_editor_property(
                        "field_of_view", float(spec.fov)
                    )
                    cam_comp.set_editor_property(
                        "constrain_aspect_ratio", False
                    )
            except Exception as exc:
                unreal.log_warning(
                    f"[UeAssetLoader] '{spec.name}': could not set FOV: {exc}"
                )

            # SceneCaptureComponent2D instances are spawned as standalone
            # actors (CameraActor does not expose add_component_by_class
            # in the Python binding) and attached to the camera actor so
            # they follow its transform.

            # ---- RGB capture actor ----------------------------------------
            rt_rgb = unreal.RenderingLibrary.create_render_target2d(
                world,
                spec.width,
                spec.height,
                unreal.TextureRenderTargetFormat.RTF_RGBA8,
            )
            cap_rgb_actor = self._actor_subsystem.spawn_actor_from_class(
                unreal.SceneCapture2D, loc, rot
            )
            cap_rgb_actor.set_actor_label(
                f"SeniorCare_CaptureRGB_{spec.name}"
            )
            cap_rgb = cap_rgb_actor.capture_component2d
            cap_rgb.set_editor_property(
                "capture_source",
                unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR,
            )
            cap_rgb.set_editor_property("texture_target", rt_rgb)
            cap_rgb.set_editor_property("capture_every_frame", True)
            cap_rgb.set_editor_property("capture_on_movement", False)
            # USceneCaptureComponent::FOVAngle is exposed to Python as
            # ``fov_angle`` (NOT ``field_of_view`` -- that's only on
            # UCameraComponent). The custom-projection-matrix toggle defaults
            # to false, so ``fov_angle`` is honored without us touching it.
            cap_rgb.set_editor_property("fov_angle", float(spec.fov))
            cap_rgb_actor.attach_to_actor(
                camera_actor,
                "",
                unreal.AttachmentRule.SNAP_TO_TARGET,
                unreal.AttachmentRule.SNAP_TO_TARGET,
                unreal.AttachmentRule.SNAP_TO_TARGET,
                False,
            )

            # ---- Depth capture actor ----------------------------------------
            # Use RTF_RGBA16f (PF_FloatRGBA) instead of RTF_R32F: only the
            # FloatRGBA family is reliably supported by
            # FRenderTarget::ReadLinearColorPixels (and therefore
            # RenderingLibrary.read_render_target_raw); single-channel R32F
            # silently returns None on most RHIs. SCS_SCENE_DEPTH writes the
            # depth value into the R channel either way, so we still read
            # ``p.r`` on the MuJoCo side. 16-bit half float gives plenty of
            # precision for the < 100 m scenes we capture.
            rt_depth = unreal.RenderingLibrary.create_render_target2d(
                world,
                spec.width,
                spec.height,
                unreal.TextureRenderTargetFormat.RTF_RGBA16F,
            )
            cap_depth_actor = self._actor_subsystem.spawn_actor_from_class(
                unreal.SceneCapture2D, loc, rot
            )
            cap_depth_actor.set_actor_label(
                f"SeniorCare_CaptureDepth_{spec.name}"
            )
            cap_depth = cap_depth_actor.capture_component2d
            cap_depth.set_editor_property(
                "capture_source",
                unreal.SceneCaptureSource.SCS_SCENE_DEPTH,
            )
            cap_depth.set_editor_property("texture_target", rt_depth)
            cap_depth.set_editor_property("capture_every_frame", False)
            cap_depth.set_editor_property("capture_on_movement", False)
            # See note above: SceneCaptureComponent2D uses ``fov_angle``.
            cap_depth.set_editor_property("fov_angle", float(spec.fov))
            cap_depth_actor.attach_to_actor(
                camera_actor,
                "",
                unreal.AttachmentRule.SNAP_TO_TARGET,
                unreal.AttachmentRule.SNAP_TO_TARGET,
                unreal.AttachmentRule.SNAP_TO_TARGET,
                False,
            )

            unreal.log(
                f"[UeAssetLoader] spawned camera '{spec.name}' at "
                f"({loc.x:.1f}, {loc.y:.1f}, {loc.z:.1f}) cm, "
                f"fov={spec.fov}°, res={spec.width}×{spec.height}"
            )
            spawned.append(
                {
                    "spec": spec,
                    "actor": camera_actor,
                    "rt_rgb": rt_rgb,
                    "rt_depth": rt_depth,
                    "cap_rgb": cap_rgb,
                    "cap_depth": cap_depth,
                }
            )

        return spawned

    # -- Material helpers ---------------------------------------------------

    _TINTABLE_MAT_PATH: str = "/Game/SeniorCare/Materials/M_SeniorCare_Tintable"

    _DEFAULT_MAT_PATHS: list[str] = [
        "/Engine/BasicShapes/BasicShapeMaterial",
        "/Engine/EngineMaterials/DefaultMaterial",
        "/Engine/EngineMaterials/WorldGridMaterial",
    ]

    _BASE_COLOR_PARAM_NAMES: tuple[str, ...] = ("BaseColor", "Color")

    def _ensure_tintable_material_exists(self) -> Any | None:
        """Return the tintable material at ``_TINTABLE_MAT_PATH``, creating
        it on the fly if it does not yet exist in the Content Browser.

        The created material has a single ``VectorParameter`` named
        ``BaseColor`` (default white) wired to the Base Color pin, with
        ``bUsedWithSkeletalMesh`` enabled so it works on PoseableMesh
        components without a shader recompile on first draw.
        """
        try:
            existing = self._editor_asset_lib.load_asset(self._TINTABLE_MAT_PATH)
            if existing is not None and isinstance(existing, unreal.MaterialInterface):
                return existing
        except Exception:
            pass

        mel = getattr(unreal, "MaterialEditingLibrary", None)
        if mel is None:
            unreal.log_warning(
                "[UeAssetLoader] MaterialEditingLibrary not available; "
                "cannot auto-create tintable material"
            )
            return None

        pkg_path = "/Game/SeniorCare/Materials"
        asset_name = "M_SeniorCare_Tintable"
        try:
            mat_factory = unreal.MaterialFactoryNew()
            mat = self._asset_tools.create_asset(
                asset_name, pkg_path, unreal.Material, mat_factory,
            )
        except Exception as exc:
            unreal.log_warning(
                f"[UeAssetLoader] create_asset for tintable material failed: {exc}"
            )
            return None

        if mat is None:
            unreal.log_warning(
                "[UeAssetLoader] create_asset returned None for tintable material"
            )
            return None

        try:
            mat.set_editor_property("used_with_skeletal_mesh", True)

            param_expr = mel.create_material_expression(
                mat, unreal.MaterialExpressionVectorParameter, -300, 0,
            )
            param_expr.set_editor_property("parameter_name", "BaseColor")
            param_expr.set_editor_property(
                "default_value", unreal.LinearColor(1.0, 1.0, 1.0, 1.0),
            )
            mel.connect_material_property(
                param_expr, "", unreal.MaterialProperty.MP_BASE_COLOR,
            )
            mel.recompile_material(mat)
            unreal.EditorAssetLibrary.save_asset(
                self._TINTABLE_MAT_PATH, only_if_is_dirty=True,
            )
        except Exception as exc:
            unreal.log_warning(
                f"[UeAssetLoader] tintable material setup failed: {exc}"
            )

        unreal.log(
            f"[UeAssetLoader] created tintable material at {self._TINTABLE_MAT_PATH}"
        )
        return mat

    def _load_first_engine_fallback_material(self) -> Any | None:
        tintable = self._ensure_tintable_material_exists()
        if tintable is not None:
            return tintable
        for path in self._DEFAULT_MAT_PATHS:
            try:
                mat = self._editor_asset_lib.load_asset(path)
                if mat is not None:
                    self._ensure_material_used_with_skeletal_mesh(mat)
                    return mat
            except Exception:
                continue
        return None

    @staticmethod
    def _ensure_material_used_with_skeletal_mesh(mat: Any) -> None:
        """Toggle ``bUsedWithSkeletalMesh`` on a UMaterial so it can shade
        skeletal/poseable meshes without UE auto-fixing it on first draw.

        The fallback engine materials (e.g. ``BasicShapeMaterial``) ship with
        this flag off, which produces the
        ``LogMaterial: ... needed to have new flag set bUsedWithSkeletalMesh``
        Display log every editor session. We only set the in-memory flag;
        we deliberately do NOT save the engine asset back to disk.
        """
        try:
            base = mat.get_base_material() if hasattr(mat, "get_base_material") else mat
        except Exception:
            base = mat
        if base is None or not isinstance(base, unreal.Material):
            return
        try:
            if not base.get_editor_property("used_with_skeletal_mesh"):
                base.set_editor_property("used_with_skeletal_mesh", True)
        except Exception as exc:
            unreal.log_warning(
                f"[UeAssetLoader] could not toggle used_with_skeletal_mesh on "
                f"'{base.get_path_name()}': {exc}"
            )

    def _resolve_parent_material_for_override(self, spec: UeAssetSpec) -> Any | None:
        """Parent ``MaterialInterface`` for instance overrides (YAML or engine default)."""
        if spec.ue_material_path:
            try:
                mat = self._editor_asset_lib.load_asset(spec.ue_material_path)
            except Exception as exc:
                unreal.log_warning(
                    f"[UeAssetLoader] '{spec.name}': ue_material "
                    f"'{spec.ue_material_path}' load failed: {exc}"
                )
                mat = None
            if mat is not None and isinstance(mat, unreal.MaterialInterface):
                unreal.log(
                    f"[UeAssetLoader] '{spec.name}': using ue_material "
                    f"{spec.ue_material_path}"
                )
                return mat
            # Asset doesn't exist yet -- auto-create if it's our tintable path.
            if spec.ue_material_path == self._TINTABLE_MAT_PATH:
                tintable = self._ensure_tintable_material_exists()
                if tintable is not None:
                    unreal.log(
                        f"[UeAssetLoader] '{spec.name}': auto-created tintable "
                        f"material at {self._TINTABLE_MAT_PATH}"
                    )
                    return tintable
            if mat is not None:
                unreal.log_warning(
                    f"[UeAssetLoader] '{spec.name}': ue_material path is not a "
                    f"MaterialInterface, falling back to engine defaults"
                )

        return self._load_first_engine_fallback_material()

    @staticmethod
    def _poseable_mesh_from_actor(actor: Any) -> Any | None:
        if hasattr(actor, "get_poseable_mesh"):
            try:
                pm = actor.get_poseable_mesh()
                if pm is not None:
                    return pm
            except Exception:
                pass
        try:
            comps = list(actor.get_components_by_class(unreal.PoseableMeshComponent))
            return comps[0] if comps else None
        except Exception:
            return None

    def _apply_material_overrides(self, actor: Any, spec: UeAssetSpec) -> None:
        """Apply per-instance materials on the PoseableMesh (YAML-driven).

        Without ``base_color``, every slot gets the same parent material (from
        ``ue_material`` if set, otherwise a built-in default).  Many FBX
        exports use empty placeholder slots; a real ``MaterialInterface``
        makes the mesh visible.  With ``base_color``, we create a dynamic
        material instance per slot and set ``BaseColor`` / ``Color`` when the
        parent exposes that scalar/vector parameter.
        """
        parent = self._resolve_parent_material_for_override(spec)
        if parent is None:
            unreal.log_warning(
                f"[UeAssetLoader] '{spec.name}': could not resolve any parent "
                f"material; mesh may be invisible"
            )
            return

        poseable = self._poseable_mesh_from_actor(actor)
        if poseable is None:
            unreal.log_warning(
                f"[UeAssetLoader] '{spec.name}': no PoseableMeshComponent "
                f"for material override"
            )
            return

        try:
            n = int(poseable.get_num_materials())
        except Exception as exc:
            unreal.log_warning(
                f"[UeAssetLoader] '{spec.name}': get_num_materials failed: {exc}"
            )
            return

        rgba = spec.base_color
        applied = 0
        tint_failed = 0
        for i in range(n):
            try:
                if rgba is not None:
                    mid = poseable.create_dynamic_material_instance(i, parent)
                    if mid is not None:
                        lc = unreal.LinearColor(
                            float(rgba[0]),
                            float(rgba[1]),
                            float(rgba[2]),
                            float(rgba[3]),
                        )
                        tinted = False
                        for pname in self._BASE_COLOR_PARAM_NAMES:
                            try:
                                mid.set_vector_parameter_value(pname, lc)
                                tinted = True
                                break
                            except Exception:
                                continue
                        if tinted:
                            applied += 1
                        else:
                            tint_failed += 1
                    else:
                        poseable.set_material(i, parent)
                        applied += 1
                else:
                    poseable.set_material(i, parent)
                    applied += 1
            except Exception as exc:
                unreal.log_warning(
                    f"[UeAssetLoader] '{spec.name}': material slot {i} "
                    f"override failed: {exc}"
                )

        if tint_failed > 0:
            tried = ", ".join(self._BASE_COLOR_PARAM_NAMES)
            unreal.log_warning(
                f"[UeAssetLoader] '{spec.name}': base_color tint failed on "
                f"{tint_failed}/{n} slot(s) -- parent material has no "
                f"parameter named {tried}. Those slots remain untinted. "
                f"Set ue_material to a material with a BaseColor "
                f"VectorParameter or use use_imported_materials: true."
            )

        tint_note = f", base_color={rgba}" if rgba else ""
        unreal.log(
            f"[UeAssetLoader] '{spec.name}': material override on "
            f"{applied}/{n} slot(s){tint_note}"
            + (f" ({tint_failed} tint failures)" if tint_failed else "")
        )

    @staticmethod
    def _get_mujoco_actor_class() -> Any:
        """Return ``unreal.MuJoCoSkeletalActor`` or raise a friendly error."""
        cls = getattr(unreal, "MuJoCoSkeletalActor", None)
        if cls is None:
            raise RuntimeError(
                "unreal.MuJoCoSkeletalActor is not available. The "
                "SeniorCareBridge C++ plugin is not loaded yet. Make "
                "sure the plugin is enabled in MyProject.uproject and "
                "the editor was allowed to rebuild missing modules on "
                "startup ('Missing modules detected -> Yes')."
            )
        return cls

    # -- Bone discovery -----------------------------------------------------

    @staticmethod
    def _bone_names_from_actor(actor: Any) -> list[str]:
        """Pull bone names from the live PoseableMesh on ``actor``.

        UE 5.1's ``UPoseableMeshComponent`` Python binding does NOT expose
        ``get_bone_names``. We instead iterate over ``get_num_bones()`` /
        ``get_bone_name(i)`` which are both UFUNCTIONs on the parent
        ``USkinnedMeshComponent`` and are reliably exposed to Python.
        """
        getter = getattr(actor, "get_poseable_mesh", None)
        poseable = getter() if callable(getter) else None
        if poseable is None:
            return []

        # Bulk accessor (UE 5.3+ has it; not present on 5.1).
        for accessor in ("get_bone_names", "GetBoneNames"):
            method = getattr(poseable, accessor, None)
            if not callable(method):
                continue
            try:
                names = list(method() or [])
                if names:
                    return [str(n) for n in names]
            except Exception as exc:
                unreal.log_warning(
                    f"[UeAssetLoader] PoseableMesh.{accessor}() failed: {exc}"
                )

        # Index iteration: get_num_bones + get_bone_name(i). Works on UE 5.1.
        get_num = getattr(poseable, "get_num_bones", None)
        get_name = getattr(poseable, "get_bone_name", None)
        if not callable(get_num) or not callable(get_name):
            unreal.log_warning(
                "[UeAssetLoader] PoseableMesh missing get_num_bones / "
                "get_bone_name UFUNCTIONs (UE Python binding too old?)"
            )
            return []
        try:
            num = int(get_num())
        except Exception as exc:
            unreal.log_warning(
                f"[UeAssetLoader] PoseableMesh.get_num_bones() failed: {exc}"
            )
            return []
        if num <= 0:
            return []
        names: list[str] = []
        for i in range(num):
            try:
                names.append(str(get_name(i)))
            except Exception as exc:
                unreal.log_warning(
                    f"[UeAssetLoader] PoseableMesh.get_bone_name({i}) failed: {exc}"
                )
                break
        return names

    @staticmethod
    def _enumerate_bone_names(skeletal_mesh: Any) -> list[str]:
        """Best-effort enumeration of bone names from the SkeletalMesh.

        Tries several accessors because UE 5.x Python exposes them under
        different spellings between point releases. We deliberately
        avoid touching any spawned component here -- this needs to work
        before the C++ actor exists (e.g. for diagnostic dumps).
        """
        if skeletal_mesh is None:
            return []
        skeleton = getattr(skeletal_mesh, "skeleton", None)

        # 1. Skeleton.get_reference_pose -> ReferenceSkeleton.bone_names.
        if skeleton is not None:
            for accessor in ("get_reference_pose", "GetReferencePose"):
                method = getattr(skeleton, accessor, None)
                if not callable(method):
                    continue
                try:
                    pose = method()
                    names = list(getattr(pose, "bone_names", None) or [])
                    if names:
                        return [str(n) for n in names]
                except Exception:
                    continue

        # 2. SkeletalMesh.get_skeleton_bone_names (rare, on some forks).
        for accessor in ("get_skeleton_bone_names", "GetSkeletonBoneNames"):
            method = getattr(skeletal_mesh, accessor, None)
            if not callable(method):
                continue
            try:
                names = list(method() or [])
                if names:
                    return [str(n) for n in names]
            except Exception:
                continue

        # 3. SkeletalMesh.skeleton.get_bone_tree() -> list of FBoneNode.
        if skeleton is not None:
            for accessor in ("get_bone_tree", "GetBoneTree"):
                method = getattr(skeleton, accessor, None)
                if not callable(method):
                    continue
                try:
                    tree = list(method() or [])
                    names = []
                    for entry in tree:
                        name = getattr(entry, "name", None) or getattr(entry, "bone_name", None)
                        if name is not None:
                            names.append(str(name))
                    if names:
                        return names
                except Exception:
                    continue

        return []

    @staticmethod
    def _fuzzy_match_bones(drivable_bones: Iterable[str], skeleton_bones: list[str]) -> dict[str, str]:
        """Map our requested bone tokens to actual skeleton bone names.

        Strategy:
            1. Exact match.
            2. Skeleton bone whose lowercase name *contains* the token.
            3. Skeleton bone whose lowercase token *contains* the bone name
               (for skeletons that strip suffixes).
        """
        skeleton_lc = {bone.lower(): bone for bone in skeleton_bones}
        mapping: dict[str, str] = {}
        for token in drivable_bones:
            if token in skeleton_bones:
                mapping[token] = token
                continue
            if token.lower() in skeleton_lc:
                mapping[token] = skeleton_lc[token.lower()]
                continue

            token_lc = token.lower()
            for bone in skeleton_bones:
                if token_lc in bone.lower():
                    mapping[token] = bone
                    break
            if token in mapping:
                continue
            for bone in skeleton_bones:
                if bone.lower() in token_lc:
                    mapping[token] = bone
                    break
        return mapping

    @staticmethod
    def _build_joint_to_bone_mapping(
        spec: UeAssetSpec,
        bone_to_control: dict[str, str],
    ) -> dict[str, dict[str, str]]:
        """Produce the JSON payload consumed by ``UMuJoCoDrivenSkeletonComponent``.

        Format::

            {
                "<mujoco_joint_name>": {"bone": "<ue_bone_name>", "axis": "z"},
                ...
            }

        For ball joints (SMPL-X human model), MuJoCo sends the full rotation
        as a quaternion (4 values: w, x, y, z). We generate 4 mapping entries
        per ball joint with axes 'w'/'x'/'y'/'z'; the C++ driver collects all
        four into a quaternion and applies the parent-bind-frame formula
        (FinalLocal = ParentWorldRest^-1 * Q_ue * ParentWorldRest * BindRot).

        For revolute joints (Franka robot), we use a single mapping with
        the default axis.
        """
        is_human = "smpl" in str(spec.mujoco_model_path or "").lower()
        joint_order: list[str] = list(spec.joint_order or spec.selected_joints)

        seen_joints: set[str] = set()
        out: dict[str, dict[str, str]] = {}

        for joint_name in joint_order:
            if joint_name in seen_joints:
                continue
            seen_joints.add(joint_name)
            bone_token = spec.bone_for_joint(joint_name)
            actual_bone = bone_to_control.get(bone_token)
            if actual_bone is None:
                continue

            if is_human:
                out[f"{joint_name}_w"] = {"bone": actual_bone, "axis": "w"}
                out[f"{joint_name}_x"] = {"bone": actual_bone, "axis": "x"}
                out[f"{joint_name}_y"] = {"bone": actual_bone, "axis": "y"}
                out[f"{joint_name}_z"] = {"bone": actual_bone, "axis": "z"}
            else:
                out[joint_name] = {"bone": actual_bone, "axis": _DEFAULT_JOINT_AXIS}
        return out


# ---------------------------------------------------------------------------
# Driver (deprecated -- C++ owns runtime joint driving now)
# ---------------------------------------------------------------------------


class UeJointDriver:
    """Back-compat shim. Real-time bone driving lives in C++ now.

    Only :meth:`set_root_pose` still does anything substantive (it just
    moves the actor's root transform, which doesn't go through the
    PoseableMesh). :meth:`set_joint_angle` and :meth:`apply_initial_state`
    are intentional no-ops -- the C++ ``UMuJoCoDrivenSkeletonComponent``
    is what reads MuJoCo frames and pushes bone rotations now. They log a
    one-shot deprecation warning so callers notice.
    """

    def __init__(self) -> None:
        self._assets: dict[str, _LoadedAsset] = {}
        self._warned_set_joint_angle: bool = False
        self._warned_apply_initial: bool = False

    # -- Registration -------------------------------------------------------

    def register(self, loaded: _LoadedAsset) -> None:
        self._assets[loaded.spec.name] = loaded

    def get(self, asset_name: str) -> _LoadedAsset:
        try:
            return self._assets[asset_name]
        except KeyError as exc:
            raise KeyError(f"Asset '{asset_name}' is not registered with UeJointDriver.") from exc

    # -- Joint driving (deprecated) ----------------------------------------

    def set_joint_angle(
        self,
        asset_name: str,
        joint_name: str,
        value: float,
        *,
        axis: str = _DEFAULT_JOINT_AXIS,
    ) -> None:
        """No-op shim. The C++ driver consumes MuJoCo frames directly."""
        del joint_name, value, axis  # unused; preserved for signature compat
        self.get(asset_name)  # raise on unknown asset, mirroring old contract
        if not self._warned_set_joint_angle:
            unreal.log_warning(
                "[UeJointDriver] set_joint_angle is a no-op since the C++ "
                "SeniorCareBridge plugin took over runtime joint driving. "
                "Drive joints by publishing MuJoCo frames over ZMQ; the "
                "UMuJoCoDrivenSkeletonComponent on each spawned actor will "
                "apply them every editor tick."
            )
            self._warned_set_joint_angle = True

    def apply_initial_state(self, asset_name: str | None = None) -> None:
        """No-op shim. Initial pose is established by the first MuJoCo frame.

        Kept for back-compat callers (``test_ue.py``,
        :func:`load_scene_for_editor`) so they don't blow up.
        """
        del asset_name
        if not self._warned_apply_initial:
            unreal.log(
                "[UeJointDriver] apply_initial_state is a no-op now; the "
                "rig will adopt the pose carried by the first MuJoCo frame "
                "the C++ subsystem receives."
            )
            self._warned_apply_initial = True

    # -- Root pose (still works) -------------------------------------------

    def set_root_pose(
        self,
        asset_name: str,
        location_cm: tuple[float, float, float],
        rotation_wxyz: tuple[float, float, float, float] | None = None,
    ) -> None:
        """Move the actor root in world space (cm).

        Refuses to move the root for assets configured with ``fix_base: true``.
        """
        loaded = self.get(asset_name)
        if loaded.spec.fix_base:
            raise RuntimeError(
                f"Asset '{asset_name}' has fix_base: true; root pose cannot be set."
            )
        actor = loaded.actor
        new_location = unreal.Vector(*location_cm)
        new_rotation = (
            _quat_wxyz_to_unreal_rotator(rotation_wxyz)
            if rotation_wxyz is not None
            else actor.get_actor_rotation()
        )
        actor.set_actor_location_and_rotation(new_location, new_rotation, False, False)


# ---------------------------------------------------------------------------
# Convenience entry point
# ---------------------------------------------------------------------------


def load_scene_for_editor(
    yaml_path: str | Path,
    *,
    clear_existing: bool = True,
    apply_initial_state: bool = True,
) -> tuple[UeScene, UeAssetLoader, UeJointDriver, list[dict]]:
    """Load a YAML scene end-to-end and return the live driver + camera list.

    Steps performed for every asset listed in the YAML:
        0. (When ``clear_existing=True``, default) Delete every actor we
           previously spawned (label prefix ``SeniorCare_``) so the level
           starts clean.
        1. ``UeAssetLoader.import_skeletal_mesh``
        2. ``UeAssetLoader.spawn_actor`` -- spawns
           ``AMuJoCoSkeletalActor`` and configures the joint -> bone mapping.
        3. Register with the (deprecated) :class:`UeJointDriver` for
           any callers that still poke joints from Python.
        4. ``UeAssetLoader.spawn_cameras`` -- spawns ``CineCameraActor``
           instances with ``SceneCaptureComponent2D`` for every entry in the
           YAML's ``cameras:`` block.

    ``apply_initial_state`` is preserved as a parameter for API
    compatibility but is now a no-op (the first MuJoCo frame establishes
    the initial pose).

    Returns
    -------
    tuple
        ``(scene, loader, driver, cameras)`` where ``cameras`` is the list
        of camera dicts returned by :meth:`UeAssetLoader.spawn_cameras`
        (empty list when no cameras are configured).
    """
    scene = UeScene.from_yaml(yaml_path)
    loader = UeAssetLoader()
    driver = UeJointDriver()

    if clear_existing:
        loader.clear_scene_actors()

    for spec in scene.specs:
        try:
            mesh, skeleton = loader.import_skeletal_mesh(spec)
            loaded = loader.spawn_actor(spec, mesh, skeleton)
            driver.register(loaded)
        except Exception as exc:
            unreal.log_error(
                f"[load_scene_for_editor] asset '{spec.name}' failed: {exc}"
            )
            continue

    cameras: list[dict] = []
    if scene.cameras:
        try:
            cameras = loader.spawn_cameras(scene.cameras)
        except Exception as exc:
            unreal.log_error(
                f"[load_scene_for_editor] camera spawning failed: {exc}"
            )

    if apply_initial_state:
        driver.apply_initial_state()
    else:
        unreal.log(
            "[load_scene_for_editor] apply_initial_state=False; "
            "skipping initial-state push (which is a no-op anyway now)."
        )
    return scene, loader, driver, cameras


__all__ = [
    "CONTENT_ROOT",
    "RIG_ROOT",
    "UeAssetLoader",
    "UeCameraSpec",
    "UeJointDriver",
    "load_scene_for_editor",
]


# Suppress "imported but unused" warnings if some tooling parses this
# file outside UE.
_ = unreal
