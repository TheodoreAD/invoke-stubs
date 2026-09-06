from typing import Any

from .collection import Collection
from .config import Config
from .parser import ParserContext, ParseResult
from .runners import Result
from .tasks import Call, Task

class Executor:
    collection: Collection
    config: Config | None
    core: ParseResult | None
    def __init__(self, collection: Collection, config: Config | None = ..., core: ParseResult | None = ...) -> None: ...
    def execute(self, *tasks: str | tuple[str, dict[str, Any]] | ParserContext) -> dict[Task[Any], Result]: ...
    def normalize(self, tasks: tuple[str | tuple[str, dict[str, Any]] | ParserContext, ...]) -> list[Call]: ...
    def dedupe(self, calls: list[Call]) -> list[Call]: ...
    def expand_calls(self, calls: list[Call]) -> list[Call]: ...
