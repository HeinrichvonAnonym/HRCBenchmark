"""MuJoCo + Zenoh + ZMQ demo loop with explicit start/stop lifecycle."""

from __future__ import annotations

import argparse
import logging
import signal
from dataclasses import dataclass
from pathlib import Path
from types import FrameType
from typing import Any, Callable

import sys

os_env = Path(__file__).resolve().parents[2]
if str(os_env) not in sys.path:
    sys.path.insert(0, str(os_env))

from benchmark.senior_care.base.mujoco_script import (  # noqa: E402
    CMD_TOPIC_DEFAULT,
    STATE_TOPIC_DEFAULT,
    SeniorCareEnv,
)


@dataclass
class MujocoRunnerConfig:
    """Configuration for :class:`MujocoRunner` (mirror of ``run_test.py`` CLI)."""

    config_path: Path
    render: bool = False
    steps: int = 2_000_000
    cmd_topic: str = CMD_TOPIC_DEFAULT
    state_topic: str = STATE_TOPIC_DEFAULT
    zmq_address: str = "tcp://localhost:5556"
    view_camera: bool = False
    zmq_camera_address: str = "tcp://localhost:5557"
    no_franka_wire: bool = False
    zenoh_scene_publish: bool = False
    zenoh_connect_endpoints: list[str] | None = None
    log_level: str = "INFO"

    @classmethod
    def from_argparse(cls, args: argparse.Namespace) -> MujocoRunnerConfig:
        return cls(
            config_path=args.config_path,
            render=args.render,
            steps=args.steps,
            cmd_topic=args.cmd_topic,
            state_topic=args.state_topic,
            zmq_address=args.zmq_address,
            view_camera=args.view_camera,
            zmq_camera_address=args.zmq_camera_address,
            no_franka_wire=args.no_franka_wire,
            zenoh_scene_publish=args.zenoh_scene_publish,
            zenoh_connect_endpoints=args.connect,
            log_level=args.log_level,
        )


class MujocoRunner:
    """Owns :class:`SeniorCareEnv`, runs the step loop until ``stop()`` or step limit."""

    def __init__(self, config: MujocoRunnerConfig) -> None:
        self._cfg = config
        self._log = logging.getLogger(__name__)
        self._env: SeniorCareEnv | None = None
        self._stop_requested = False
        self._previous_sigint: Callable[..., Any] | int | None = None

    def stop(self, reason: str = "stop() called") -> None:
        """Request shutdown and release resources (idempotent)."""
        self._stop_requested = True
        env = self._env
        if env is None:
            return
        self._log.info("[MujocoRunner] stop: %s", reason)
        self._env = None
        try:
            env.close()
        except Exception as exc:
            self._log.warning("[MujocoRunner] env.close() failed: %s", exc)

    def _on_sigint(self, signum: int, frame: FrameType | None) -> None:
        del signum, frame
        self.stop("SIGINT (Ctrl+C)")

    def _install_sigint(self) -> None:
        self._previous_sigint = signal.signal(signal.SIGINT, self._on_sigint)

    def _restore_sigint(self) -> None:
        if self._previous_sigint is not None:
            signal.signal(signal.SIGINT, self._previous_sigint)
            self._previous_sigint = None

    def start(self) -> None:
        """Build env, reset, run until ``steps``, viewer exit, or ``stop()``."""
        self._stop_requested = False
        cfg = self._cfg

        logging.basicConfig(
            level=getattr(logging, cfg.log_level.upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
            force=True,
        )

        self._install_sigint()
        try:
            self._env = SeniorCareEnv(
                cfg.config_path,
                zenoh_publish=cfg.zenoh_scene_publish,
                zenoh_franka_topics=not cfg.no_franka_wire,
                zenoh_cmd_topic=cfg.cmd_topic,
                zenoh_state_topic=cfg.state_topic,
                zenoh_connect_endpoints=cfg.zenoh_connect_endpoints,
                zmq_publish=True,
                zmq_address=cfg.zmq_address,
                view_camera=cfg.view_camera,
                zmq_camera_address=cfg.zmq_camera_address,
            )
            env = self._env
            env.reset()
            action = env.home_action()

            print(
                f"Zenoh (env): cmd={cfg.cmd_topic!r} state={cfg.state_topic!r}  "
                f"franka_topics={not cfg.no_franka_wire} "
                f"scene_publish={cfg.zenoh_scene_publish}  zmq={cfg.zmq_address!r}  "
                f"view_camera={cfg.view_camera}  camera_addr={cfg.zmq_camera_address!r}",
            )

            if cfg.render:
                import mujoco.viewer

                with mujoco.viewer.launch_passive(env.model, env.data) as viewer:
                    n = 0
                    while (
                        n < cfg.steps
                        and viewer.is_running()
                        and not self._stop_requested
                    ):
                        with viewer.lock():
                            env.step(action)
                        viewer.sync()
                        n += 1
            else:
                for _ in range(cfg.steps):
                    if self._stop_requested:
                        break
                    env.step(action)
        finally:
            self._restore_sigint()
            if self._env is not None:
                self.stop("start() finished or interrupted")
