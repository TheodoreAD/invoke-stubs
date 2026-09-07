from collections.abc import Iterable
from typing import Any

class Argument:
    attr_name: str | None
    default: Any | None
    help: str | None
    incrementable: bool
    kind: Any
    names: tuple[str, ...]
    optional: bool
    positional: bool
    # Not a constructor parameter: it starts as `None`, `[]` for a list-kind argument, or the
    # default for an incrementable one, and the parser then assigns whatever came off the command
    # line.
    raw_value: Any
    def __init__(
        self,
        name: str | None = ...,
        names: Iterable[str] = ...,
        kind: Any = ...,
        default: Any | None = ...,
        # invoke's own keyword name; renaming it here would describe an API that does not exist.
        help: str | None = ...,  # noqa: A002
        positional: bool = ...,
        optional: bool = ...,
        incrementable: bool = ...,
        attr_name: str | None = ...,
    ) -> None: ...
    @property
    def name(self) -> str | None: ...
    @property
    def nicknames(self) -> tuple[str, ...]: ...
    @property
    def takes_value(self) -> bool: ...
    @property
    def value(self) -> Any: ...
    @value.setter
    def value(self, arg: str) -> None: ...
    def set_value(self, value: Any, cast: bool = ...) -> None: ...
    @property
    def got_value(self) -> bool: ...
