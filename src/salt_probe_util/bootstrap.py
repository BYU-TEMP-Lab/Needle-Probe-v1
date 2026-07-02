import os
import sys
import warnings
import logging
from datetime import datetime
from pathlib import Path


# Custom warning format to show relative paths and omit source code line

def relative_showwarning(message, category, filename, lineno, file=None, line=None):
    # 1. Generate the relative path
    rel_path = os.path.relpath(filename)
    short_path = os.path.basename(rel_path)
    
    # 2. Build the output string
    # IMPORTANT: We DO NOT include the 'line' variable here. 
    # This is what removes the redundant source code line.
    # output = f"{rel_path}:{lineno}: {category.__name__}: {message}\n"
    output = f"{short_path}:{lineno}: {category.__name__}: {message}\n"
    
    # 3. Explicitly write to the output stream (usually stderr)
    if file is None:
        file = sys.stderr
    try:
        file.write(output)
    except (AttributeError, OSError):
        pass


def setup_logging(log_dir=None, level=logging.INFO):
    """Configure shared project logging for console and file output."""
    logger = logging.getLogger("salt_probe_util")

    requested_log_dir = Path(log_dir or Path.cwd() / "logs")
    requested_log_dir.mkdir(parents=True, exist_ok=True)

    if getattr(setup_logging, "_configured", False):
        existing_log_dir = getattr(setup_logging, "_log_dir", None)
        if existing_log_dir is not None and Path(existing_log_dir).resolve() == requested_log_dir.resolve():
            return logger, getattr(setup_logging, "_log_path", None)

    log_path = requested_log_dir / f"run_{datetime.now():%Y%m%d_%H%M%S}.log"

    logger.setLevel(level)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(name)s:%(lineno)d: %(message)s")

    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(formatter)
    fh.setLevel(level)
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(formatter)
    sh.setLevel(level)
    logger.addHandler(sh)

    logging.captureWarnings(True)
    warnings.showwarning = relative_showwarning
    warnings.filterwarnings("always")

    logger.info("Logging initialized")
    logger.info("Log file: %s", log_path)

    setup_logging._configured = True
    setup_logging._log_path = log_path
    setup_logging._log_dir = requested_log_dir
    return logger, log_path