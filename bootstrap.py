import  os, sys, warnings
# Custom warning format to show relative paths and omit source code line

def relative_showwarning(message, category, filename, lineno, file=None, line=None):
    # 1. Generate the relative path
    rel_path = os.path.relpath(filename)
    
    # 2. Build the output string
    # IMPORTANT: We DO NOT include the 'line' variable here. 
    # This is what removes the redundant source code line.
    output = f"{rel_path}:{lineno}: {category.__name__}: {message}\n"
    
    # 3. Explicitly write to the output stream (usually stderr)
    if file is None:
        file = sys.stderr
    try:
        file.write(output)
    except (AttributeError, OSError):
        pass

def setup_logging():
    # Apply the override to showwarning (the action) rather than formatwarning (the string)
    warnings.showwarning = relative_showwarning

    # Ensure the filter allows your warnings to be seen during testing
    warnings.filterwarnings('always')