# Not re-exported by `invoke/__init__.py`, but required all the same: `runners` and `exceptions`
# take `ExceptionHandlingThread`/`ExceptionWrapper` from here, and `program` takes `Lexicon`.
#
# `Lexicon` is declared here rather than imported from `.vendor.lexicon`, which this distribution
# deliberately does not ship. invoke's own `util.py` imports it from the vendored copy and every
# other module of invoke then takes it from `util`, so this is the spelling the rest of invoke
# actually uses; the vendored path is not reachable from any stub here and so cannot diverge.

import logging
import threading
from collections.abc import Callable, Generator
from contextlib import contextmanager
from types import TracebackType
from typing import IO, Any, NamedTuple

LOG_FORMAT: str
log: logging.Logger
debug: Callable[..., None]

class Lexicon(dict[str, Any]):
    def __getattr__(self, name: str) -> Any: ...
    def __setattr__(self, name: str, value: Any) -> None: ...
    def alias(self, from_: str, to: str) -> None: ...
    def aliases_of(self, name: str) -> list[str]: ...

class ExceptionWrapper(NamedTuple):
    kwargs: dict[str, Any]
    type: type[BaseException] | None
    value: BaseException | None
    traceback: TracebackType | None

def enable_logging() -> None: ...
def task_name_sort_key(name: str) -> tuple[list[str], str]: ...
@contextmanager
def cd(where: str) -> Generator[None]: ...
def has_fileno(stream: IO[Any]) -> bool: ...
def isatty(stream: IO[Any]) -> bool: ...
def helpline(obj: object) -> str | None: ...

class ExceptionHandlingThread(threading.Thread):
    exc_info: tuple[type[BaseException], BaseException, TracebackType] | tuple[None, None, None] | None
    kwargs: dict[str, Any]
    def __init__(self, **kwargs: Any) -> None: ...
    def run(self) -> None: ...
    def exception(self) -> ExceptionWrapper | None: ...
    @property
    def is_dead(self) -> bool: ...
