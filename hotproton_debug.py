from __future__ import print_function

import logging
import os


_LOGGER_NAME = "hotproton"
_TRUE_VALUES = frozenset(("1", "true", "yes", "on", "debug"))


def _debug_enabled_from_environment():
    value = os.environ.get("HOTPROTON_DEBUG", "")
    return value.strip().lower() in _TRUE_VALUES


def configure_debug(enabled=None):
    """Configure HotPROTON debug logging and return its enabled state."""
    if enabled is None:
        enabled = _debug_enabled_from_environment()

    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            "[HotPROTON] %(levelname)s %(name)s: %(message)s"
        ))
        logger.addHandler(handler)

    logger.setLevel(logging.DEBUG if enabled else logging.WARNING)
    logger.propagate = False
    return enabled


def get_logger(module_name):
    """Return a logger controlled by the HOTPROTON_DEBUG environment variable."""
    configure_debug()
    return logging.getLogger("{}.{}".format(_LOGGER_NAME, module_name))
