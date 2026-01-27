from pathlib import Path

def get_size(file_path: Path) -> str:
    try:
        size = file_path.stat().st_size
    except OSError:
        return "unknown"

    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"


