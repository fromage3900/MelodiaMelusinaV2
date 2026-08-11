"""surreal_greybox — extracted greybox primitives and snap helpers (v2.66)."""

from .primitives import attach_to_monolith as attach_primitives
from .snaps import attach_to_monolith as attach_snaps
from .shells import attach_to_monolith as attach_shells


def attach_all(monolith):
    attach_primitives(monolith)
    attach_snaps(monolith)
    attach_shells(monolith)
