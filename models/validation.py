def require_int(
    value: int,
    name: str,
    minimum: int = 1,
    maximum: int | None = None,
) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name}: требуется целое число от {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name}: значение должно быть не больше {maximum}")
    return value


def require_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}: требуется непустая строка")
    return value.strip()


def require_bool(value: bool, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name}: требуется true или false")
    return value
