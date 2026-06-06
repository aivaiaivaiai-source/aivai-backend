def clamp_limit(limit: int, max_limit: int = 100) -> int:
    if limit < 1:
        return 1
    if limit > max_limit:
        return max_limit
    return limit
