from __future__ import annotations

# Keep agent modules importable from `agents/` while the primary
# implementation lives at the repo root (requested: `origin_bot.py`).

from origin_bot import OriginBot


__all__ = ["OriginBot"]
