"""Lightweight ZMQ PUB / SUB base class.

Handles context lifecycle and provides helpers for send/recv JSON frames.
Subclasses (MujocoZmqSession, UeZmqSession) add domain-specific logic.

``import zmq`` is intentionally deferred to the first call that actually
opens a socket so this module can be imported in environments where the
``zmq`` package is not installed (e.g. UE's embedded Python when only
``camera_signal`` / ``UeZmqSession`` are needed).
"""

from __future__ import annotations

import json
import os
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    import zmq


class ZmqSession:
    """Thin wrapper around a single ZMQ socket (PUB *or* SUB).

    Parameters
    ----------
    address : ZMQ address string, e.g. ``tcp://*:5556`` or ``tcp://localhost:5556``.
    """

    def __init__(self, address: str = "tcp://localhost:5556") -> None:
        self._address = address
        # Context and socket are created lazily on first open_pub / open_sub call.
        self._context: zmq.Context | None = None
        self._socket: zmq.Socket | None = None

    def _get_context(self) -> zmq.Context:
        """Return (and lazily create) the ZMQ context."""
        if self._context is None:
            import zmq as _zmq
            self._context = _zmq.Context()
        return self._context

    # -- PUB helpers -------------------------------------------------------

    def open_pub(self, *, bind: bool | None = None) -> None:
        """Create a PUB socket and either *bind* or *connect*.

        When *bind* is ``None`` (default) the env-var
        ``SENIOR_CARE_ZMQ_BIND`` is checked (``"1"`` → bind, ``"0"`` → connect);
        default is **bind**.
        """
        import zmq as _zmq

        if bind is None:
            bind = os.environ.get("SENIOR_CARE_ZMQ_BIND", "1") != "0"

        self._socket = self._get_context().socket(_zmq.PUB)
        if bind:
            self._socket.bind(self._address)
        else:
            self._socket.connect(self._address)

    # -- SUB helpers -------------------------------------------------------

    def open_sub(self, *, recv_timeout_ms: int = 100) -> None:
        """Create a SUB socket that *connects* to the PUB address."""
        import zmq as _zmq

        self._socket = self._get_context().socket(_zmq.SUB)
        self._socket.setsockopt(_zmq.SUBSCRIBE, b"")
        self._socket.setsockopt(_zmq.RCVTIMEO, recv_timeout_ms)
        self._socket.connect(self._address)

    # -- I/O ---------------------------------------------------------------

    def send_json(self, obj: Any) -> None:
        """Serialize *obj* as JSON and send through the PUB socket."""
        assert self._socket is not None, "call open_pub() first"
        self._socket.send(json.dumps(obj).encode())

    def recv_json(self) -> dict | None:
        """Non-blocking receive; returns parsed dict or ``None`` on timeout."""
        if self._socket is None:
            return None
        try:
            raw = self._socket.recv()
            return json.loads(raw)
        except Exception:
            # zmq.Again (timeout) and any other error both return None.
            return None

    def send_multipart(self, parts: list[bytes]) -> None:
        """Send a multipart message through the PUB socket.

        Used for RGBD camera frames where each part carries a different
        data type (JSON header, raw RGB bytes, raw depth bytes).
        """
        assert self._socket is not None, "call open_pub() first"
        self._socket.send_multipart(parts)

    def recv_multipart(self) -> list[bytes] | None:
        """Non-blocking multipart receive; returns list of byte frames or ``None``."""
        if self._socket is None:
            return None
        try:
            return self._socket.recv_multipart()
        except Exception:
            return None

    # -- lifecycle ---------------------------------------------------------

    def close(self) -> None:
        if self._socket is not None:
            self._socket.close()
            self._socket = None
        if self._context is not None:
            self._context.term()
            self._context = None

    def __del__(self) -> None:
        self.close()
