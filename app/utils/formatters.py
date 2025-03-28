def format_large_number(number):
    """Format large numbers to K, M, B, T format for both integers and floats, and handle scientific notation."""
    
    if number >= 1_000_000_000_000:
        return f"{number/1_000_000_000_000:.1f}T"
    elif number >= 1_000_000_000:
        return f"{number/1_000_000_000:.1f}B"
    elif number >= 1_000_000:
        return f"{number/1_000_000:.1f}M"
    elif number >= 1_000:
        return f"{number/1_000:.1f}K"
    return str(int(number))

