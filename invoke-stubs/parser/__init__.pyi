# `invoke.parser` is a package upstream, so it is one here too — a flat `parser.pyi` would resolve
# the package but leave `invoke.parser.context` and its siblings unresolvable, and under a
# non-partial marker there is no inline version left to fall back to.

from .argument import Argument as Argument
from .context import (
    ParserContext as ParserContext,
)
from .context import (
    flag_key as flag_key,
)
from .context import (
    sort_candidate as sort_candidate,
)
from .context import (
    to_flag as to_flag,
)
from .context import (
    translate_underscores as translate_underscores,
)
from .parser import (
    ParseMachine as ParseMachine,
)
from .parser import (
    Parser as Parser,
)
from .parser import (
    ParseResult as ParseResult,
)
from .parser import (
    is_flag as is_flag,
)
from .parser import (
    is_long_flag as is_long_flag,
)

# invoke's own alias for `ParserContext` within this package. Spelled as an assignment rather than a
# second `import ... as`, which an import sorter splits into a duplicate import of the same module.
Context = ParserContext
