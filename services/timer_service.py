def format_seconds_to_hms(seconds: int) -> str:
    """Formats an integer number of seconds into HH:MM:SS string."""
    hrs = seconds // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hrs:02d}:{mins:02d}:{secs:02d}"
