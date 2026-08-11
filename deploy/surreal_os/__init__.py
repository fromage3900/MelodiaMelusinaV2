"""Surreal Architecture OS — Style Genome, atoms, grammar, rules."""

from .genome import apply_genome, get_genome, list_genomes, load_genome
from .grammar_loader import load_grammar_graph, merge_grammar_into_registry
from .atoms import list_atoms, resolve_atom

__all__ = [
    "apply_genome",
    "get_genome",
    "list_genomes",
    "load_genome",
    "load_grammar_graph",
    "merge_grammar_into_registry",
    "list_atoms",
    "resolve_atom",
]
