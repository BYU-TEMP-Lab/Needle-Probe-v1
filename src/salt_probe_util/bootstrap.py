import  os, sys, warnings, logging
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

def setup_logging(log_dir: str | Path | None = None, level: int = logging.INFO):
    """
    Configure project logging. If `log_dir` is provided it will be used
    as the folder for the timestamped log file (use the raw-data folder).
    Otherwise a `logs/` folder at the project root is created.
    Idempotent: calling multiple times is safe.
    """
    if getattr(setup_logging, "_configured", False):
        return

    # Basic root logger configuration (console)
    logger = logging.getLogger()
    logger.setLevel(level)
    fmt = "%(asctime)s %(levelname)-8s %(name)s:%(lineno)d: %(message)s"
    formatter = logging.Formatter(fmt)

    # Stream handler to stderr
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(formatter)
    sh.setLevel(level)
    logger.addHandler(sh)

    # Determine log folder
    if log_dir:
        log_folder = Path(log_dir)
    else:
        # project root: two parents up from this file (src/salt_probe_util -> project root)
        log_folder = Path(__file__).resolve().parents[2] / "logs"
    log_folder.mkdir(parents=True, exist_ok=True)

    # Timestamped file handler
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_file = log_folder / f"run_{ts}.log"
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(formatter)
    fh.setLevel(level)
    logger.addHandler(fh)

    # Route warnings through logging and apply the compact warning formatter
    logging.captureWarnings(True)
    warnings.showwarning = relative_showwarning
    warnings.filterwarnings("always")

    logger.info("Logging initialized")
    logger.info(f"Log file: {log_file}")

    setup_logging._configured = True
    return log_file