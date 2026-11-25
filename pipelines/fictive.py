"""Fictive stay generation — common primitives for sampling hospital stays.

This module provides shared building blocks for generating fictitious
hospital stays from PMSI data. It is used by both the PMSI sampling and profile-generation
pipelines to ensure consistent sampling logic and reduce code duplication.

Responsibilities:
- Generate fictitious hospital stays from PMSI data (PMSI sampling/profile-generation).
- Ensure consistent sampling logic across pipelines.
- Reduce code duplication between pipelines.

Public API:
- :func:`generate_fictive_stays`: Generate fictitious stays for a given pipeline.
"""

from __future__ import annotations

from typing import Any

import polars as pl

# ---------------------------------------------------------------------------
# Common fictive-generation helpers
# ---------------------------------------------------------------------------


def generate_fictive_stays(
    data: dict[str, pl.LazyFrame],
    generate_fn,
    n_sejours: int = 1000,
    **kwargs: Any,
) -> pl.DataFrame:
    """Generate fictitious stays via weighted PMSI sampling.

    Parameters
    ----------
    data:
        Dict of LazyFrames returned by the pipeline's ``load_data`` method.
    n_sejours:
        Number of fictitious stays to generate.
    generate_fn:
        Function to generate dictive stay
    **kwargs:
        Additional pipeline-specific arguments (e.g., ``n_ccam``, ``n_das``
        for PMSI sampling; ``seed`` for profile-generation).

    Returns
    -------
    pl.DataFrame
        One row per fictitious stay. Columns depend on the pipeline type.
    """
    return generate_fn(data, n_sejours, **kwargs)
