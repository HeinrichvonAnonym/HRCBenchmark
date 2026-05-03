"""UE-side ZMQ session – receives simulation state frames from MuJoCo
and (optionally) publishes RGBD camera frames back to MuJoCo."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .zmq_session import ZmqSession

if TYPE_CHECKING:
    import zmq
    from .camera_signal import CameraFrame


class UeZmqSession(ZmqSession):
    """Wraps ZMQ sockets for the UE side of the MuJoCo ↔ UE bridge.

    **Asset-state channel** (existing, port 5556 by default)
        SUB socket — receives per-step simulation state published by
        ``MujocoZmqSession.publish_step``.

    **Camera channel** (new, port 5557 by default)
        PUB socket — publishes RGBD frames captured inside UE back to the
        MuJoCo process (``MujocoZmqSession.recv_camera_frame``).

    Typical usage inside ``UESeniorCareEnv`` / editor tick::

        self._zmq = UeZmqSession(address, recv_timeout_ms=100)
        self._zmq.open_sub()
        self._zmq.open_camera_pub("tcp://*:5557")
        ...
        frame = self._zmq.recv_frame()
        if frame is not None:
            apply_to_actors(frame)
        ...
        self._zmq.send_camera_frame(camera_frame)
        ...
        self._zmq.close()

    Parameters
    ----------
    address : ZMQ address for the asset-state SUB socket, e.g.
        ``tcp://localhost:5556``.
    recv_timeout_ms : Receive timeout in milliseconds; after this
        ``recv_frame`` returns ``None`` so the caller can check a stop flag.
    """

    def __init__(
        self,
        address: str = "tcp://localhost:5556",
        recv_timeout_ms: int = 100,
    ) -> None:
        super().__init__(address)
        self._recv_timeout_ms = recv_timeout_ms
        self._camera_socket: zmq.Socket | None = None  # type: ignore[type-arg]

    # ------------------------------------------------------------------
    # Asset-state channel (SUB)
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Camera channel (PUB)
    # ------------------------------------------------------------------

    def open_camera_pub(
        self,
        address: str = "tcp://*:5557",
        *,
        bind: bool = True,
    ) -> None:
        """Open the camera PUB socket.

        Parameters
        ----------
        address : ZMQ bind/connect address, e.g. ``tcp://*:5557``.
        bind    : When ``True`` (default) the socket *binds*; set to
            ``False`` to *connect* instead (e.g. when a broker sits
            between UE and MuJoCo).
        """
        import zmq as _zmq

        self._camera_socket = self._get_context().socket(_zmq.PUB)
        # LINGER=0 so close() drops any unsent frames immediately and the OS
        # releases the port right away. Without this, re-running the script
        # while UE keeps the previous interpreter alive (or after a crash)
        # often hits "Address already in use" because the kernel still has
        # the port in TIME_WAIT / FIN_WAIT for the old socket.
        self._camera_socket.setsockopt(_zmq.LINGER, 0)
        if bind:
            self._camera_socket.bind(address)
        else:
            self._camera_socket.connect(address)

    def send_camera_frame(self, frame: "CameraFrame") -> None:
        """Publish one RGBD frame over the camera PUB socket.

        Parameters
        ----------
        frame : A :class:`~camera_signal.CameraFrame` with populated
            ``rgb_bytes`` and ``depth_bytes``.

        Raises
        ------
        AssertionError : If ``open_camera_pub`` has not been called yet.
        """
        assert self._camera_socket is not None, "call open_camera_pub() first"
        self._camera_socket.send_multipart(frame.to_multipart())

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close both the asset-state SUB and camera PUB sockets."""
        if self._camera_socket is not None:
            self._camera_socket.close()
            self._camera_socket = None
        super().close()
