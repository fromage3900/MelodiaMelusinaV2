"""surreal_greybox — extracted greybox primitives and snap helpers (v2.66).

Reconstructed 2026-08-23 from surviving bytecode after a deploy-tree /MIR
dropped the untracked original. Aggregates the three core attach points;
corridors/facades/towers patch through shells.attach_to_monolith's mapping.
"""

from . import primitives, shells, snaps


def attach_primitives(monolith):
    primitives.attach_to_monolith(monolith)


def attach_shells(monolith):
    shells.attach_to_monolith(monolith)


def attach_snaps(monolith):
    snaps.attach_to_monolith(monolith)


def attach_to_monolith(monolith):
    attach_all(monolith)


def attach_all(monolith):
    attach_primitives(monolith)
    attach_shells(monolith)
    attach_snaps(monolith)
