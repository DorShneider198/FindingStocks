"""Lightweight structured logging for ingestion (stdlib only, no new dependency).

Library code: modules get a logger via ``get_logger(__name__)`` and emit
consistent ``key=value`` event lines via ``info`` / ``warning`` / ``error``. We
deliberately **do not** attach handlers or call ``basicConfig`` here — configuring
output is the application's job. ``configure_logging`` is an opt-in convenience for
tests, a REPL, or a future entry point.

Never log credentials or payloads: emit only ``source``, ``ticker``, small counts,
and exception *types* — never User-Agents, client secrets, ``.info`` dicts, or post
bodies.
"""

from __future__ import annotations

import logging


def get_logger(name: str) -> logging.Logger:
    """Return the module-level logger for ``name`` (typically ``__name__``)."""
    return logging.getLogger(name)


def event(logger: logging.Logger, level: int, name: str, *, exc_info: bool = False, **fields) -> None:
    """Emit one structured event: ``name key=value key=value ...``.

    ``None``-valued fields are dropped. String building is skipped when the level
    is disabled. ``exc_info=True`` attaches the current traceback (errors only).
    """
    if not logger.isEnabledFor(level):
        return
    parts = " ".join(f"{k}={v}" for k, v in fields.items() if v is not None)
    message = f"{name} {parts}" if parts else name
    logger.log(level, message, exc_info=exc_info)


def info(logger: logging.Logger, name: str, **fields) -> None:
    """Emit an INFO event."""
    event(logger, logging.INFO, name, **fields)


def warning(logger: logging.Logger, name: str, **fields) -> None:
    """Emit a WARNING event (e.g. a fetch that returned empty/partial data)."""
    event(logger, logging.WARNING, name, **fields)


def error(logger: logging.Logger, name: str, *, exc_info: bool = True, **fields) -> None:
    """Emit an ERROR event, with the traceback attached by default."""
    event(logger, logging.ERROR, name, exc_info=exc_info, **fields)


def configure_logging(level: int = logging.INFO) -> None:
    """Opt-in handler setup for tests / REPL / a future entry point.

    Not called by library code. Safe to call once at process start.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
