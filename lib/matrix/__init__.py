"""Matrix expansion module."""

from lib.matrix.expander import MatrixExpander, RunSpec, PairSpec
from lib.matrix.id_generator import (
    generate_experiment_id,
    generate_run_id,
    generate_pair_id,
    compute_invariant_hash,
)

__all__ = [
    "MatrixExpander",
    "RunSpec",
    "PairSpec",
    "generate_experiment_id",
    "generate_run_id",
    "generate_pair_id",
    "compute_invariant_hash",
]
