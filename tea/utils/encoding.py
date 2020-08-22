def smart_text(s, encoding="utf-8", errors="strict"):
    """Return a unicode object representing 's'.

    Treats bytes using the 'encoding' codec.
    """
    if isinstance(s, str):
        return s

    if isinstance(s, bytes):
        return s.decode(encoding, errors)

    return str(s)


def smart_bytes(s, encoding="utf-8", errors="strict"):
    """Return a bytes version of 's' encoded as specified in 'encoding'."""
    if isinstance(s, bytes):
        if encoding == "utf-8":
            return s
        else:
            return s.decode("utf-8", errors).encode(encoding, errors)

    if isinstance(s, str):
        return s.encode(encoding, errors)

    return str(s).encode(encoding, errors)
