from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass
class AssetAction:
    position: dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_any(cls, raw: Any) -> "AssetAction":
        if isinstance(raw, cls):
            return raw
        if isinstance(raw, Mapping):
            values = raw.get("position", {})
            if isinstance(values, Mapping):
                return cls(position={str(k): float(v) for k, v in values.items()})
            return cls(position={})
        return cls(position={})

    def to_dict(self) -> dict[str, dict[str, float]]:
        return {"position": dict(self.position)}


@dataclass
class ActionMessage:
    assets: dict[str, AssetAction] = field(default_factory=dict)

    @classmethod
    def from_any(cls, raw: Any) -> "ActionMessage":
        if isinstance(raw, cls):
            return raw
        if not isinstance(raw, Mapping):
            raise TypeError("Action must be a mapping keyed by asset name.")
        return cls(
            assets={
                str(asset_name): AssetAction.from_any(asset_action)
                for asset_name, asset_action in raw.items()
            }
        )

    def to_dict(self) -> dict[str, dict[str, dict[str, float]]]:
        return {
            asset_name: asset_action.to_dict()
            for asset_name, asset_action in self.assets.items()
        }


def zeros_from_selected_joints(
    selected_joints: Mapping[str, Sequence[str]],
) -> ActionMessage:
    return ActionMessage(
        assets={
            asset_name: AssetAction(position={name: 0.0 for name in joint_names})
            for asset_name, joint_names in selected_joints.items()
        }
    )
