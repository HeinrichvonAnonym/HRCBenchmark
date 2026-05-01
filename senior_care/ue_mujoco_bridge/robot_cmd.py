"""Robot state frame transmitted over ZMQ from MuJoCo to UE."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RobotFrame:
    """One robot's state in a single simulation step.

    Attributes
    ----------
    root_position : [x, y, z] in meters (MuJoCo frame).
    root_orientation : [w, x, y, z] quaternion (MuJoCo frame).
    joints : {joint_name: position_rad} for every observation channel.
    bone_transforms : reserved UE skeletal-bone transform map.
    """
    root_position: list[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    root_orientation: list[float] = field(default_factory=lambda: [1.0, 0.0, 0.0, 0.0])
    joints: dict[str, float] = field(default_factory=dict)
    bone_transforms: dict[str, dict[str, list[float]]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "root_position": self.root_position,
            "root_orientation": self.root_orientation,
            "joints": self.joints,
            "bone_transforms": self.bone_transforms,
        }

    @classmethod
    def from_dict(cls, d: dict) -> RobotFrame:
        return cls(
            root_position=d.get("root_position", [0.0, 0.0, 0.0]),
            root_orientation=d.get("root_orientation", [1.0, 0.0, 0.0, 0.0]),
            joints=d.get("joints", {}),
            bone_transforms=d.get("bone_transforms", {}),
        )
