"""ZMQ wire format for RGBD camera frames.

``CameraFrame`` is transmitted from the UE publisher to the MuJoCo subscriber
over a dedicated ZMQ PUB/SUB channel (default port 5557, reverse direction to
the asset-state channel on port 5556).

Wire format — 3-part ZMQ multipart message
-------------------------------------------
Part 0 : JSON header (camera metadata, see fields below).
Part 1 : raw RGB bytes  — H×W×3, dtype uint8, row-major.
Part 2 : raw depth bytes — H×W,   dtype float32 little-endian, **metres**.

The dataclass stores ``rgb_bytes`` / ``depth_bytes`` as plain ``bytes`` so
that it can be constructed and serialised on the UE side where numpy is
typically not available.  Numpy convenience accessors are provided for the
MuJoCo side.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np


@dataclass
class CameraFrame:
    """One RGBD snapshot from a virtual camera in the UE scene.

    Attributes
    ----------
    camera_name : Matches the ``name`` key under ``cameras:`` in demo.yaml.
    seq         : Monotonically increasing frame counter (per-camera).
    timestamp   : Wall-clock seconds since the tick callback was registered.
    width, height : Image resolution in pixels.
    fov         : Horizontal field-of-view in degrees.
    position    : Camera centre in MuJoCo world frame, metres [x, y, z].
    orientation : Camera orientation as quaternion [w, x, y, z].
    rgb_bytes   : Raw H×W×3 uint8 pixel data (R, G, B order, row-major).
    depth_bytes : Raw H×W float32 depth data, little-endian, metres.
                  Zero / negative values indicate no geometry (sky).
    """

    camera_name: str
    seq: int
    timestamp: float
    width: int
    height: int
    fov: float
    position: list[float]
    orientation: list[float]
    rgb_bytes: bytes
    depth_bytes: bytes

    # ------------------------------------------------------------------
    # Numpy accessors (MuJoCo / CPython side only — numpy required)
    # ------------------------------------------------------------------

    def rgb_array(self) -> "np.ndarray":
        """Return a ``(height, width, 3)`` uint8 numpy array (RGB order)."""
        import numpy as _np
        return _np.frombuffer(self.rgb_bytes, dtype=_np.uint8).reshape(
            self.height, self.width, 3
        )

    def depth_array(self) -> "np.ndarray":
        """Return a ``(height, width)`` float32 numpy array in metres."""
        import numpy as _np
        return _np.frombuffer(self.depth_bytes, dtype=_np.float32).reshape(
            self.height, self.width
        )

    # ------------------------------------------------------------------
    # Serialisation (numpy-free — works in UE Python)
    # ------------------------------------------------------------------

    def to_multipart(self) -> list[bytes]:
        """Encode as a 3-part ZMQ multipart message.

        Returns
        -------
        list of bytes
            ``[header_json, rgb_bytes, depth_bytes]``
        """
        header = {
            "camera_name": self.camera_name,
            "seq": self.seq,
            "timestamp": self.timestamp,
            "width": self.width,
            "height": self.height,
            "fov": self.fov,
            "position": self.position,
            "orientation": self.orientation,
        }
        return [json.dumps(header).encode(), self.rgb_bytes, self.depth_bytes]

    @classmethod
    def from_multipart(cls, parts: list[bytes]) -> "CameraFrame":
        """Decode from a 3-part ZMQ multipart message.

        Parameters
        ----------
        parts : ``[header_json, rgb_bytes, depth_bytes]``
        """
        if len(parts) != 3:
            raise ValueError(
                f"CameraFrame.from_multipart expects 3 parts, got {len(parts)}"
            )
        header: dict = json.loads(parts[0])
        return cls(
            camera_name=str(header["camera_name"]),
            seq=int(header["seq"]),
            timestamp=float(header["timestamp"]),
            width=int(header["width"]),
            height=int(header["height"]),
            fov=float(header["fov"]),
            position=list(header["position"]),
            orientation=list(header["orientation"]),
            rgb_bytes=bytes(parts[1]),
            depth_bytes=bytes(parts[2]),
        )


__all__ = ["CameraFrame"]
