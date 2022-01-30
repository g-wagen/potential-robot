import unicodedata


def convert_unicode_fractions(char: str) -> float:
    """
    Convert those unicode fractions `1/4`, `2/3`, etc. to `float`.

    ---
    Parameters:\n
    `char` (str):\n
    Unicode or any character.

    ---
    `returns` (float):\n
    Will error if `char` can't be converted
    to it's numeric representation.
    """

    output = None
    output = str(unicodedata.numeric(char))

    return output
