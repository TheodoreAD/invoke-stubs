# Overrides only `invoke.tasks`; every other module keeps invoke's inline (`py.typed`) annotations.
# invoke declares `task(*args, **kwargs) -> Callable` — a bare `Callable`, i.e. `Callable[..., Any]`
# — so `@task` erases the decorated function's signature for every caller: pyright reports
# `reportUntypedFunctionDecorator` at each decorator and "partially unknown" wherever a task is
# referenced. The `ParamSpec` overloads below make a decorated task keep its own parameters and
# return type, and `Task.__call__` forwards them.

from collections.abc import Callable, Iterable
from inspect import Signature
from typing import Any, Generic, ParamSpec, TypeVar, overload

from .config import Config
from .context import Context
from .parser import Argument

P = ParamSpec("P")
R = TypeVar("R")
T = TypeVar("T", bound=Callable[..., Any])

class Task(Generic[T]):
    body: T
    aliases: Iterable[str]
    is_default: bool
    positional: list[str]
    optional: tuple[str, ...]
    iterable: Iterable[str]
    incrementable: Iterable[str]
    auto_shortflags: bool
    help: dict[str, Any]
    # Narrower than `__init__`'s parameter on purpose: a task object is what a `pre=[...]` list holds
    # in practice, and `Call` answers `.name` too (its `__getattr__` delegates to the task).
    pre: list[Task[Any] | Call]
    post: list[Task[Any] | Call]
    times_called: int
    autoprint: bool
    __name__: str
    __module__: str
    def __init__(
        self,
        body: T,
        name: str | None = None,
        aliases: Iterable[str] = (),
        positional: Iterable[str] | None = None,
        optional: Iterable[str] = (),
        default: bool = False,
        auto_shortflags: bool = True,
        help: dict[str, Any] | None = None,  # noqa: A002 — invoke's own keyword name
        pre: list[Task[Any] | Call | str] | str | None = None,
        post: list[Task[Any] | Call | str] | str | None = None,
        autoprint: bool = False,
        iterable: Iterable[str] | None = None,
        incrementable: Iterable[str] | None = None,
    ) -> None: ...
    @property
    def name(self) -> str: ...
    def __call__(self: Task[Callable[P, R]], *args: P.args, **kwargs: P.kwargs) -> R: ...
    @property
    def called(self) -> bool: ...
    def argspec(self, body: Callable[..., Any]) -> Signature: ...
    def fill_implicit_positionals(self, positional: Iterable[str] | None) -> list[str]: ...
    def arg_options(self, name: str, default: Any, taken_names: set[str]) -> dict[str, Any]: ...
    def get_arguments(self, ignore_unknown_help: bool | None = None) -> list[Argument]: ...

@overload
def task(body: Callable[P, R], /) -> Task[Callable[P, R]]: ...
@overload
def task(
    *pre_tasks: Task[Any] | Call,
    name: str | None = ...,
    aliases: Iterable[str] = ...,
    positional: Iterable[str] | None = ...,
    optional: Iterable[str] = ...,
    default: bool = ...,
    auto_shortflags: bool = ...,
    help: dict[str, Any] | None = ...,  # noqa: A002 — invoke's own keyword name
    pre: list[Task[Any] | Call | str] | str | None = ...,
    post: list[Task[Any] | Call | str] | str | None = ...,
    autoprint: bool = ...,
    iterable: Iterable[str] | None = ...,
    incrementable: Iterable[str] | None = ...,
    klass: type[Task[Any]] = ...,
) -> Callable[[Callable[P, R]], Task[Callable[P, R]]]: ...

class Call:
    task: Task[Any]
    called_as: str | None
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    def __init__(
        self,
        task: Task[Any],
        called_as: str | None = None,
        args: tuple[Any, ...] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> None: ...
    def __getattr__(self, name: str) -> Any: ...
    def __deepcopy__(self, memo: object) -> Call: ...
    def __eq__(self, other: object) -> bool: ...
    def make_context(self, config: Config) -> Context: ...
    def clone_data(self) -> dict[str, Any]: ...
    def clone(self, into: type[Call] | None = None, with_: dict[str, Any] | None = None) -> Call: ...

def call(task: Task[Any], *args: Any, **kwargs: Any) -> Call: ...
