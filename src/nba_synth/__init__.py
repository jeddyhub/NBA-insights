"""
NBA-synth package
=================

Tools for:
1. Synthesizing quarter-by-quarter NBA game statistics
2. Performing feature analysis + clustering
3. Generating conjectures on features via TxGraffiti
"""

from .synthetic import synthesize_quarters
from .features import analyze_features
from .conjectures import generate_conjectures

__all__ = [
    "synthesize_quarters",
    "analyze_features",
    "generate_conjectures",
]