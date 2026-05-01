"""UE-side ZMQ subscriber – receives simulation state frames from MuJoCo."""

from __future__ import annotations

from typing import Any

from .zmq_session import ZmqSession


class UeZmqSession(ZmqSession):
    """Wraps a ZMQ SUB socket that receives per-step simulation state.

    Typical usage inside ``UESeniorCareEnv``::

        self._zmq = UeZmqSession(address, recv_timeout_ms=100)
        self._zmq.open_sub()
        ...
        frame = self._zmq.recv_frame()
        if frame is not None:
            apply_to_actors(frame)
        ...
        self._zmq.close()

    Parameters
    ----------
    address : ZMQ address to connect to, e.g. ``tcp://localhost:5556``.
    recv_timeout_ms : Receive timeout in milliseconds; after this the recv
        returns ``None`` so the caller can check a stop flag.
    """

    def __init__(
        self,
        address: str = "tcp://localhost:5556",
        recv_timeout_ms: int = 100,
    ) -> None:
        super().__init__(address)
        self._recv_timeout_ms = recv_timeout_ms

    def open_sub(self, *, recv_timeout_ms: int | None = None) -> None:
        """Open the SUB socket with the configured timeout."""
        timeout = recv_timeout_ms if recv_timeout_ms is not None else self._recv_timeout_ms
        super().open_sub(recv_timeout_ms=timeout)

    def recv_frame(self) -> dict[str, Any] | None:
        """Receive one JSON frame, or ``None`` on timeout / error.

        Returns the same dict structure published by
        ``MujocoZmqSession.publish_step``::

            {
                "seq": int,
                "assets": { "<name>": { ... }, ... }
            }
        """
        return self.recv_json()
