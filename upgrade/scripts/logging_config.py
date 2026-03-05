import logging
import sys
from logging.handlers import WatchedFileHandler
from pathlib import Path
from typing import Optional, Tuple

DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
UPGRADE_HANDLER_ATTR = "_upgrade_handler"


class _MaxLevelFilter(logging.Filter):
    def __init__(self, max_level: int):
        super().__init__()
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno < self.max_level


def _is_upgrade_handler(handler: logging.Handler) -> bool:
    return bool(getattr(handler, UPGRADE_HANDLER_ATTR, False))


def _mark_upgrade_handler(handler: logging.Handler) -> None:
    setattr(handler, UPGRADE_HANDLER_ATTR, True)


def _remove_upgrade_handlers(root: logging.Logger) -> None:
    for handler in list(root.handlers):
        if _is_upgrade_handler(handler):
            root.removeHandler(handler)
            handler.close()


def get_error_log_path(log_location: str) -> str:
    log_path = Path(log_location)
    if log_path.suffix:
        return str(log_path.with_name(f"{log_path.stem}.error{log_path.suffix}"))
    return f"{log_location}.error.log"


def configure_logging(
    *,
    log_location: Optional[str],
    default_log_location: str,
    test: bool,
    level: int = logging.INFO,
) -> Tuple[Optional[str], Optional[str]]:
    root = logging.getLogger()
    _remove_upgrade_handlers(root)
    has_foreign_handlers = any(
        not _is_upgrade_handler(handler) for handler in root.handlers
    )

    formatter = logging.Formatter(DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DATE_FORMAT)

    if test:
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setLevel(level)
        stream_handler.setFormatter(formatter)
        _mark_upgrade_handler(stream_handler)
        root.addHandler(stream_handler)
        if not has_foreign_handlers:
            root.setLevel(level)
        return None, None

    regular_log_path = log_location or default_log_location
    error_log_path = get_error_log_path(regular_log_path)

    regular_handler = WatchedFileHandler(regular_log_path)
    regular_handler.setLevel(level)
    regular_handler.addFilter(_MaxLevelFilter(logging.ERROR))
    regular_handler.setFormatter(formatter)
    _mark_upgrade_handler(regular_handler)

    error_handler = WatchedFileHandler(error_log_path)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    _mark_upgrade_handler(error_handler)

    root.addHandler(regular_handler)
    root.addHandler(error_handler)
    if not has_foreign_handlers:
        root.setLevel(level)
    return regular_log_path, error_log_path


def configure_script_logging(
    *,
    log_location: Optional[str],
    default_log_location: str,
    test: bool,
) -> Tuple[Optional[str], Optional[str]]:
    try:
        return configure_logging(
            log_location=log_location,
            default_log_location=default_log_location,
            test=test,
            level=logging.DEBUG if test else logging.INFO,
        )
    except Exception as logging_config_error:
        configure_logging(
            log_location=None,
            default_log_location=default_log_location,
            test=True,
            level=logging.INFO,
        )
        logging.warning(
            "Failed to configure file logging at %s; falling back to stderr logging: %s",
            log_location or default_log_location,
            logging_config_error,
        )
        return None, None


def _summary_value(value: Optional[object]) -> str:
    if value is None:
        return "unknown"
    value_text = str(value)
    if value_text == "":
        return "unknown"
    return value_text


def log_run_summary(
    *,
    script: str,
    package: Optional[str],
    current: Optional[object],
    target: Optional[object],
    final: Optional[object],
    result: str,
    duration_seconds: float,
) -> None:
    logging.info(
        "summary script=%s package=%s current=%s target=%s final=%s result=%s duration_s=%.2f",
        script,
        _summary_value(package),
        _summary_value(current),
        _summary_value(target),
        _summary_value(final),
        result,
        duration_seconds,
    )
