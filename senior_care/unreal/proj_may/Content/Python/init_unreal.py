"""Auto-loaded by UE on editor startup (PythonScriptPlugin convention).

Prepends our project-local ``Content/Python/Lib`` directory to ``sys.path``
so packages installed there with ``--target`` (currently just pyyaml) are
importable from in-editor scripts like ``test_ue.py``.

UE itself already adds ``Content/Python`` to sys.path; we just augment it.
"""

from __future__ import annotations

import sys
from pathlib import Path


_LIB_DIR = Path(__file__).resolve().parent / "Lib"


def _ensure_on_sys_path(path: Path) -> None:
    s = str(path)
    if s not in sys.path:
        sys.path.insert(0, s)


if _LIB_DIR.is_dir():
    _ensure_on_sys_path(_LIB_DIR)
    try:
        import unreal  # type: ignore[import-not-found]

        unreal.log(f"[init_unreal] prepended {_LIB_DIR} to sys.path")
    except Exception:
        # ``unreal`` import could fail if this file is ever executed outside
        # the editor (it shouldn't be); silently swallow.
        pass
