def format_large_number(number):
    """Format large numbers to K, M, B, T format for both integers and floats, and handle scientific notation."""
    number = float(number)

    if abs(number) >= 1_000_000_000_000:
        return f"{number/1_000_000_000_000:.2f}T"
    elif abs(number) >= 1_000_000_000:
        return f"{number/1_000_000_000:.2f}B"
    elif abs(number) >= 1_000_000:
        return f"{number/1_000_000:.2f}M"
    elif abs(number) >= 1_000:
        return f"{number/1_000:.2f}K"
    else:
        return f"{number:.2f}"

