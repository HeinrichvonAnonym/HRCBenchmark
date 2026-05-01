"""Lightweight ZMQ PUB / SUB base class.

Handles context lifecycle and provides helpers for send/recv JSON frames.
Subclasses (MujocoZmqSession, UeZmqSession) add domain-specific logic.
"""

from __future__ import annotations

import json
import os
from typing import Any

import zmq


class ZmqSession:
    """Thin wrapper around a single ZMQ socket (PUB *or* SUB).

    Parameters
    ----------
    address : ZMQ address string, e.g. ``tcp://*:5556`` or ``tcp://localhost:5556``.
    """

    def __init__(self, address: str = "tcp://localhost:5556") -> None:
        self._address = address
        self._context: zmq.Context | None = zmq.Context()
        self._socket: zmq.Socket | None = None

    # -- PUB helpers -------------------------------------------------------

    def open_pub(self, *, bind: bool | None = None) -> None:
        """Create a PUB socket and either *bind* or *connect*.

        When *bind* is ``None`` (default) the env-var
        ``SENIOR_CARE_ZMQ_BIND`` is checked (``"1"`` → bind, ``"0"`` → connect);
        default is **bind**.
        """
        if bind is None:
            bind = os.environ.get("SENIOR_CARE_ZMQ_BIND", "1") != "0"

        assert self._context is not None
        self._socket = self._context.socket(zmq.PUB)
        if bind:
            self._socket.bind(self._address)
        else:
            self._socket.connect(self._address)

    # -- SUB helpers -------------------------------------------------------

    def open_sub(self, *, recv_timeout_ms: int = 100) -> None:
        """Create a SUB socket that *connects* to the PUB address."""
        assert self._context is not None
        self._socket = self._context.socket(zmq.SUB)
        self._socket.setsockopt(zmq.SUBSCRIBE, b"")
        self._socket.setsockopt(zmq.RCVTIMEO, recv_timeout_ms)
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
        except zmq.Again:
            return None
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
