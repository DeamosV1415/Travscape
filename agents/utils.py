from datetime import datetime

def get_today_str() -> str:
    """Get current date in a human-readable format."""
    # Use %#d for Windows, %-d for Unix, fallback to %d if neither is available
    try:
        return datetime.now().strftime("%a %b %#d, %Y")
    except ValueError:
        try:
            return datetime.now().strftime("%a %b %-d, %Y")
        except ValueError:
            return datetime.now().strftime("%a %b %d, %Y")