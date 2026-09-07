from collections.abc import Iterable
from typing import Any

class Argument:
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
