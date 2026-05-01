from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AssetObservation:
    root_position: list[float]
    root_orientation: list[float]
    position: dict[str, float | list[float]] = field(default_factory=dict)
    velocity: dict[str, float | list[float]] = field(default_factory=dict)
    effort: dict[str, float | list[float]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return {
            "root_position": list(self.root_position),
            "root_orientation": list(self.root_orientation),
            "position": dict(self.position),
            "velocity": dict(self.velocity),
            "effort": dict(self.effort),
        }


@dataclass
class ObservationMessage:
    assets: dict[str, AssetObservation] = field(default_factory=dict)

    def to_dict(self) -> dict[str, dict[str, object]]:
        return {
            asset_name: asset_observation.to_dict()
            for asset_name, asset_observation in self.assets.items()
        }
