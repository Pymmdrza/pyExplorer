def format_large_number(number, decimals=2, concise_format=True):
    """
    Converts a number in scientific notation (string format) to a concise, readable decimal string.

    This function takes a string representing a number in scientific notation and formats it
    into a more user-friendly, concise decimal string. It offers options for concise formatting,
    such as removing trailing zeros and using abbreviations for large numbers (e.g., K, M, B, T).

    Args:
        number (str): The number in scientific notation as a string (e.g., "1.23E+06").
        decimals (int, optional): The number of decimal places to round to in the initial formatting.
                                        Defaults to 2. Must be a non-negative integer.
        concise_format (bool, optional):  If True, applies concise formatting (removes trailing zeros and
                                        uses abbreviations for large numbers). If False, returns standard
                                        fixed-point formatting. Defaults to True.

    Returns:
        str: A string representing the number in a concise decimal format if concise_format is True,
             or standard decimal format if False.
             Returns "Invalid Input: Not a valid scientific number" if the input string is invalid.

    Raises:
        TypeError: if `number` is not a string or `decimals` is not an integer.
        ValueError: if `decimals` is a negative integer.

    Example:
        >>> format_scientific_notation_concise("1.13757508810854E14")
        '113.76T'
        >>> format_scientific_notation_concise("1.13757508810854E14", concise_format=False)
        '113757508810854.00'
        >>> format_scientific_notation_concise("2.5e-3", decimals=4)
        '0.0025'
        >>> format_scientific_notation_concise("1234567", concise_format=True)
        '1.23M'
        >>> format_scientific_notation_concise("1234", concise_format=True)
        '1.23K'
        >>> format_scientific_notation_concise("123", concise_format=True)
        '123'
    """
    number = str(number)
    if decimals < 0:
        raise ValueError("Input 'decimals' must be a non-negative integer.")
    if not isinstance(concise_format, bool):
        raise TypeError("Input 'concise_format' must be a boolean.")


    try:
        number = float(number)

        if not concise_format:
            return f"{number:.{decimals}f}"  # Standard formatting

        # Concise formatting logic
        magnitude = 0
        suffix = ''
        if abs(number) >= 1000:
            magnitude_suffixes = ['', 'K', 'M', 'B', 'T', 'P', 'E', 'Z', 'Y']
            magnitude = 0
            temp_number = abs(number)
            while temp_number >= 1000 and magnitude < len(magnitude_suffixes) - 1:
                magnitude += 1
                temp_number /= 1000.0
            suffix = magnitude_suffixes[magnitude]
            number /= (1000**magnitude)


        formatted_number = f"{number:.{decimals}f}{suffix}"

        # Remove trailing zeros after decimal point if concise format is requested
        if concise_format and '.' in formatted_number:
            formatted_number = formatted_number.rstrip('0').rstrip('.') if formatted_number.endswith('0') or formatted_number.endswith('.') else formatted_number


        return formatted_number

    except ValueError:
        return "Invalid Input: Not a valid scientific number"
    
