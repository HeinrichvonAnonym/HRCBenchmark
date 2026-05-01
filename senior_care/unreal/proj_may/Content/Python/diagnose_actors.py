"""Two-in-one editor utility:

1) Dial PostProcessVolume bias back from the over-bright +10 to a sensible
   value so the scene isn't blown out.
2) Walk every MuJoCoSkeletalActor in the level and dump:
       * its PoseableMeshComponent reference
       * the SkeletalMesh currently assigned to it
       * the SkeletalMesh's bounding box (lets us see if the mesh exists and
         where it actually lives in world space -- "wrong kinematic chain"
         often means the mesh is at scale 0 or the bounds collapsed)
       * the material slot list (a SkeletalMesh with no/black materials
         renders as a wireframe outline only -- exactly what the user is
         seeing)
       * the bone count + first 8 bone names

Run from the Output Log:

    py "/home/heinrich/RoboLab/python/benchmark/senior_care/unreal/proj_may/Content/Python/diagnose_actors.py"
"""

from __future__ import annotations

import unreal


PPV_TAG = "fix_dark_scene_ppv"
DESIRED_BIAS_STOPS = 2


def _has_tag(actor, tag: str) -> bool:
    try:
        tags = [str(t) for t in (actor.tags or [])]
    except Exception:
        return False
    return tag in tags


def _dial_back_exposure(all_actors) -> None:
    target = None
    for a in all_actors:
        if isinstance(a, unreal.PostProcessVolume):
            if _has_tag(a, PPV_TAG):
                target = a
                break
            if target is None:
                target = a
    if target is None:
        unreal.log_warning("[diagnose_actors] no PostProcessVolume found")
        return
    s = target.settings
    s.override_auto_exposure_bias = True
    s.auto_exposure_bias = DESIRED_BIAS_STOPS
    target.settings = s
    unreal.log(
        f"[diagnose_actors] PostProcessVolume bias -> {DESIRED_BIAS_STOPS} stops"
    )


def _component_chain_summary(actor) -> str:
    parts = []
    try:
        comps = list(actor.get_components_by_class(unreal.SceneComponent))
    except Exception:
        comps = []
    for c in comps:
        try:
            cls = c.get_class().get_name()
        except Exception:
            cls = "?"
        parts.append(cls)
    return f"[{len(parts)} components] " + ", ".join(parts)


def _dump_skeletal(actor) -> None:
    label = actor.get_actor_label()
    loc = actor.get_actor_location()
    scale = actor.get_actor_scale3d()
    unreal.log(
        f"[diagnose_actors] === {label} === at "
        f"({loc.x:.1f},{loc.y:.1f},{loc.z:.1f}) scale=({scale.x},{scale.y},{scale.z})"
    )

    unreal.log(f"  components: {_component_chain_summary(actor)}")

    poseable = None
    try:
        if hasattr(actor, "get_poseable_mesh"):
            poseable = actor.get_poseable_mesh()
    except Exception as exc:
        unreal.log_warning(f"  get_poseable_mesh() raised: {exc}")
    if poseable is None:
        try:
            poseables = list(actor.get_components_by_class(unreal.PoseableMeshComponent))
            poseable = poseables[0] if poseables else None
        except Exception:
            poseable = None
    if poseable is None:
        unreal.log_warning("  -> NO PoseableMeshComponent found on this actor!")
        return

    mesh = None
    for getter in ("get_skinned_asset", "skeletal_mesh", "skeletal_mesh_asset"):
        try:
            attr = getattr(poseable, getter, None)
            if callable(attr):
                mesh = attr()
            else:
                mesh = attr
            if mesh is not None:
                break
        except Exception:
            continue

    if mesh is None:
        unreal.log_warning(
            "  -> PoseableMeshComponent has NO skinned asset! "
            "set_skinned_asset() probably silently failed."
        )
    else:
        try:
            mesh_path = mesh.get_path_name()
        except Exception:
            mesh_path = "?"
        unreal.log(f"  skinned asset: {mesh_path}")

        try:
            num_bones = poseable.get_num_bones()
            unreal.log(f"  poseable num_bones: {num_bones}")
            sample = []
            for i in range(min(8, int(num_bones))):
                try:
                    sample.append(str(poseable.get_bone_name(i)))
                except Exception:
                    break
            unreal.log(f"  first bones: {sample}")
        except Exception as exc:
            unreal.log_warning(f"  could not enumerate bones: {exc}")

        try:
            bounds = poseable.calc_local_bounds()
            unreal.log(
                f"  poseable local bounds: origin=({bounds.origin.x:.1f},"
                f"{bounds.origin.y:.1f},{bounds.origin.z:.1f}) "
                f"extent=({bounds.box_extent.x:.1f},{bounds.box_extent.y:.1f},"
                f"{bounds.box_extent.z:.1f})"
            )
        except Exception as exc:
            unreal.log_warning(f"  could not get poseable bounds: {exc}")

        try:
            mat_count = poseable.get_num_materials()
            mats_info = []
            for i in range(int(mat_count)):
                try:
                    m = poseable.get_material(i)
                    if m is None:
                        mats_info.append(f"#{i}=None")
                    else:
                        mats_info.append(f"#{i}={m.get_name()}")
                except Exception:
                    mats_info.append(f"#{i}=?")
            unreal.log(
                f"  poseable materials ({mat_count}): " + ", ".join(mats_info)
            )
        except Exception as exc:
            unreal.log_warning(f"  could not enumerate materials: {exc}")

        try:
            visible = poseable.get_editor_property("visible")
            hidden_in_game = poseable.get_editor_property("hidden_in_game")
            unreal.log(
                f"  poseable visible={visible} hidden_in_game={hidden_in_game}"
            )
        except Exception:
            pass


def main() -> None:
    ed = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    all_actors = list(ed.get_all_level_actors())

    _dial_back_exposure(all_actors)

    skeletal_actors = [
        a for a in all_actors
        if a.get_class().get_name() == "MuJoCoSkeletalActor"
    ]
    unreal.log(
        f"[diagnose_actors] found {len(skeletal_actors)} MuJoCoSkeletalActor(s)"
    )
    if not skeletal_actors:
        unreal.log_warning(
            "  -> none. Either the bridge plugin didn't register the class, "
            "or test_ue.py never ran successfully."
        )

    for actor in skeletal_actors:
        _dump_skeletal(actor)

    try:
        unreal.EditorLevelLibrary.editor_invalidate_viewports()
    except Exception:
        pass


main()
