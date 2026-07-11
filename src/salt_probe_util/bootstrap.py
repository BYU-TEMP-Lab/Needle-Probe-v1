import os
import sys
import warnings
import logging
from datetime import datetime
from pathlib import Path
import shutil

def update_log_destination(new_log_dir):
    """
    Dynamically shifts the active logging destination to a new directory.
    Moves the existing log file and updates all active FileHandlers.
    """
    # 1. Verification of current configuration state
    if not getattr(setup_logging, "_configured", False):
        raise RuntimeError("Logging must be initialized via setup_logging before updating destination.")

    current_path = Path(setup_logging._log_path)
    new_log_dir = Path(new_log_dir)
    new_log_dir.mkdir(parents=True, exist_ok=True)
    new_path = new_log_dir / current_path.name

    # If the paths resolve to the same file, no action is required
    if current_path.resolve() == new_path.resolve():
        return setup_logging._log_path

    # 2. Safely release file locks on the current log file
    loggers_to_update = [
        logging.getLogger("salt_probe_util"),
        logging.getLogger("py.warnings")
    ]

    # Collect and close active FileHandlers
    file_handlers = []
    for logger in loggers_to_update:
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                handler.close()  # Flushes and releases the OS file handle
                file_handlers.append((logger, handler))

    # 3. Relocate the log file on disk
    try:
        shutil.move(str(current_path), str(new_path))
    except Exception as e:
        # Fallback: Re-open handlers on failure to prevent loss of logs
        for logger, handler in file_handlers:
            handler.baseFilename = os.path.abspath(current_path)
        raise IOError(f"Failed to move log file to {new_path}: {e}")

    # 4. Re-target the FileHandlers to the new destination path
    for logger, handler in file_handlers:
        # Mutate the target path inside the existing handler object
        handler.baseFilename = os.path.abspath(new_path)
        
        # Trigger the logger's internal stream re-initialization
        # This re-opens the file stream automatically upon the next log event
        handler.stream = None 

    # 5. Synchronize the global cache state on setup_logging
    setup_logging._log_path = new_path
    setup_logging._log_dir = new_log_dir

    # Log completion using the updated pipeline
    main_logger = logging.getLogger("salt_probe_util")
    main_logger.info("Log destination successfully updated to: %s", new_path)

    return new_path

def setup_logging(log_dir=None, level=logging.DEBUG):
    """Configure shared project logging for console and file output."""
    # initialize / reinitialize master logger
    logger = logging.getLogger("salt_probe_util")

    requested_log_dir = Path(log_dir or Path.cwd() / "logs")
    requested_log_dir.mkdir(parents=True, exist_ok=True)

    if getattr(setup_logging, "_configured", False):
        existing_log_dir = getattr(setup_logging, "_log_dir", None)
        existing_level = getattr(setup_logging, "_level", None)
        if (existing_log_dir is not None and 
            Path(existing_log_dir).resolve() == requested_log_dir.resolve()):
            if level < existing_level:
                logger.setLevel(level)
                for handler in logger.handlers:
                    handler.setLevel(level)
                setup_logging._level = level
            logger.debug("Logging already configured; reusing existing configuration.")
            return logger, getattr(setup_logging, "_log_path", None)

    log_path = requested_log_dir / f"run_{datetime.now():%Y%m%d_%H%M%S}.log"

    # set up parent logger (if changes have been made)
    logger.setLevel(level)
    logger.handlers.clear()
    logger.propagate = True  # Allow propagation to root logger if needed

    # set up warning logger
    warn_logger = logging.getLogger("py.warnings")
    warn_logger.setLevel(level)
    warn_logger.handlers.clear()
    warn_logger.propagate = False  # Prevent double logging of warnings

    # distinguish between console and log file formatting
    console_formatter = logging.Formatter("%(levelname)-5s [%(filename)s:%(lineno)d] %(message)s")
    file_formatter = logging.Formatter("%(asctime)s %(levelname)-8s %(name)s:%(lineno)d: %(message)s", datefmt="%H:%M:%S")

    # file handler
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(file_formatter)
    fh.setLevel(level)
    logger.addHandler(fh)
    warn_logger.addHandler(fh)

    # stream handler
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(console_formatter)
    sh.setLevel(level)
    logger.addHandler(sh)
    warn_logger.addHandler(sh)

    # capture warnings and ensure they are always shown (may change later)
    logging.captureWarnings(True)
    warnings.filterwarnings("always")

    # log the initialization
    logger.info("Logging initialized")
    logger.info("Log file: %s", log_path.name)

    # flags to prevent reconfiguration and store log path
    setup_logging._configured = True
    setup_logging._log_path = log_path
    setup_logging._log_dir = requested_log_dir
    setup_logging._level = level
    return logger, log_path