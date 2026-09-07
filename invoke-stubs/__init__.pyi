# The names invoke's own `__init__.py` re-exports, in the `import X as X` form PEP 484 requires for a
# re-export to count as public in a typed package. invoke uses a plain `from .tasks import task`
# with a lint suppression, which type checkers read as an implementation detail — so
# `from invoke import task` reports
# `reportPrivateImportUsage` (pyright) / `no_implicit_reexport` (mypy --strict) against the inline
# package.
#
# Every module named below is shipped here, plus `util`, which several of them need. `py.typed`
# stays `partial` deliberately: `env`, `completion`, `main` and the vendored packages are not
# shipped, and the marker is what keeps those resolvable for a consumer that does have invoke
# installed. See plans/2026-08-30-missing-collection-and-context-stubs.md section 4 for why that is
# the end state rather than a step towards a complete distribution.

from typing import Any

from .collection import Collection as Collection
from .config import Config as Config
from .context import Context as Context
from .context import MockContext as MockContext
from .exceptions import (
    AmbiguousEnvVar as AmbiguousEnvVar,
)
from .exceptions import (
    AuthFailure as AuthFailure,
)
from .exceptions import (
    CollectionNotFound as CollectionNotFound,
)
from .exceptions import (
    CommandTimedOut as CommandTimedOut,
)
from .exceptions import (
    Exit as Exit,
)
from .exceptions import (
    ParseError as ParseError,
)
from .exceptions import (
    PlatformError as PlatformError,
)
from .exceptions import (
    ResponseNotAccepted as ResponseNotAccepted,
)
from .exceptions import (
    SubprocessPipeError as SubprocessPipeError,
)
from .exceptions import (
    ThreadException as ThreadException,
)
from .exceptions import (
    UncastableEnvVar as UncastableEnvVar,
)
from .exceptions import (
    UnexpectedExit as UnexpectedExit,
)
from .exceptions import (
    UnknownFileType as UnknownFileType,
)
from .exceptions import (
    UnpicklableConfigMember as UnpicklableConfigMember,
)
from .exceptions import (
    WatcherError as WatcherError,
)
from .executor import Executor as Executor
from .loader import FilesystemLoader as FilesystemLoader
from .parser import (
    Argument as Argument,
)
from .parser import (
    Parser as Parser,
)
from .parser import (
    ParserContext as ParserContext,
)
from .parser import (
    ParseResult as ParseResult,
)
from .program import Program as Program
from .runners import (
    Failure as Failure,
)
from .runners import (
    Local as Local,
)
from .runners import (
    Promise as Promise,
)
from .runners import (
    Result as Result,
)
from .runners import (
    Runner as Runner,
)
from .tasks import Call as Call
from .tasks import Task as Task
from .tasks import call as call
from .tasks import task as task
from .terminals import pty_size as pty_size
from .watchers import (
    FailingResponder as FailingResponder,
)
from .watchers import (
    Responder as Responder,
)
from .watchers import (
    StreamWatcher as StreamWatcher,
)

__version__: str

def run(command: str, **kwargs: Any) -> Result: ...
def sudo(command: str, **kwargs: Any) -> Result: ...
