import threading
from typing import Generator, Iterable

class StreamWatcher(threading.local):
    def submit(self, stream: str) -> Iterable[str]: ...

class Responder(StreamWatcher):
    index: int
    pattern: str
    response: str
    def __init__(self, pattern: str, response: str) -> None: ...
    def pattern_matches(self, stream: str, pattern: str, index_attr: str) -> Iterable[str]: ...
    def submit(self, stream: str) -> Generator[str, None, None]: ...

class FailingResponder(Responder):
    failure_index: int
    sentinel: str
    tried: bool
    def __init__(self, pattern: str, response: str, sentinel: str) -> None: ...
    def submit(self, stream: str) -> Generator[str, None, None]: ...
