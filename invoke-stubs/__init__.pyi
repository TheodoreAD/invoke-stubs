# The names invoke's own `__init__.py` re-exports, in the `import X as X` form PEP 484 requires for a
# re-export to count as public in a typed package. invoke uses plain `from .tasks import task  # noqa`,
# which type checkers read as an implementation detail — so `from invoke import task` reports
# `reportPrivateImportUsage` (pyright) / `no_implicit_reexport` (mypy --strict) against the inline
# package. Everything except `.tasks` resolves to invoke's inline annotations (`py.typed` = partial).

from .collection import Collection as Collection
from .config import Config as Config
from .context import Context as Context, MockContext as MockContext
from .exceptions import (
    AmbiguousEnvVar as AmbiguousEnvVar,
    AuthFailure as AuthFailure,
    CollectionNotFound as CollectionNotFound,
    CommandTimedOut as CommandTimedOut,
    Exit as Exit,
    ParseError as ParseError,
    PlatformError as PlatformError,
    ResponseNotAccepted as ResponseNotAccepted,
    SubprocessPipeError as SubprocessPipeError,
    ThreadException as ThreadException,
    UncastableEnvVar as UncastableEnvVar,
    UnexpectedExit as UnexpectedExit,
    UnknownFileType as UnknownFileType,
    UnpicklableConfigMember as UnpicklableConfigMember,
    WatcherError as WatcherError,
)
from .executor import Executor as Executor
from .loader import FilesystemLoader as FilesystemLoader
from .parser import (
    Argument as Argument,
    Parser as Parser,
    ParserContext as ParserContext,
    ParseResult as ParseResult,
)
from .program import Program as Program
from .runners import (
    Failure as Failure,
    Local as Local,
    Promise as Promise,
    Result as Result,
    Runner as Runner,
)
from .tasks import Call as Call, Task as Task, call as call, task as task
from .terminals import pty_size as pty_size
from .watchers import (
    FailingResponder as FailingResponder,
    Responder as Responder,
    StreamWatcher as StreamWatcher,
)
from typing import Any

__version__: str

def run(command: str, **kwargs: Any) -> Result: ...
def sudo(command: str, **kwargs: Any) -> Result: ...
