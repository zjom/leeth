from typing import NoReturn


def todo(msg: str = "", *args: object, **kwargs: object) -> NoReturn:
    """Mark unfinished code, like Rust's todo!()."""
    if msg:
        raise NotImplementedError(f"not yet implemented: {msg.format(*args, **kwargs)}")
    raise NotImplementedError("not yet implemented")
