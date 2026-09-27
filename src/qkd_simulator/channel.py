"""
Quantum channel models for the QKD simulator.

This module models two simplified channel imperfections:

1. Channel loss:
   A transmitted quantum signal may be lost before reaching Bob.

2. Channel noise:
   A surviving signal may experience a bit-flip error.

The models are intentionally simple. They are designed to study the
statistical impact of channel imperfections on BB84 performance rather
than reproduce a detailed optical communication channel.
"""

from __future__ import annotations

import numpy as np


def _validate_probability(
    probability: float,
    name: str,
) -> None:
    """
    Validate that a probability lies in the interval [0, 1].
    """
    if not 0.0 <= probability <= 1.0:
        raise ValueError(
            f"{name} must be between 0 and 1."
        )


def apply_channel_loss(
    n_signals: int,
    loss_probability: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Determine which transmitted signals survive the channel.

    Each signal independently survives with probability:

        1 - loss_probability

    Parameters
    ----------
    n_signals:
        Number of transmitted signals.

    loss_probability:
        Probability that an individual signal is lost.

    rng:
        NumPy random number generator.

    Returns
    -------
    np.ndarray
        Boolean array where:

        True  -> signal reaches Bob
        False -> signal is lost
    """
    if n_signals <= 0:
        raise ValueError(
            "n_signals must be greater than zero."
        )

    _validate_probability(
        loss_probability,
        "loss_probability",
    )

    random_values = rng.random(n_signals)

    surviving_mask = random_values >= loss_probability

    return surviving_mask


def apply_channel_noise(
    bits: np.ndarray,
    noise_probability: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Apply independent bit-flip noise to transmitted bits.

    Each bit is independently flipped with probability
    `noise_probability`.

    Parameters
    ----------
    bits:
        Binary values carried by the surviving signals.

    noise_probability:
        Probability that a bit is flipped by the channel.

    rng:
        NumPy random number generator.

    Returns
    -------
    np.ndarray
        Noisy copy of the input bits.

    Notes
    -----
    This is a simplified noise model. It represents the effect of
    channel imperfections at the level relevant to QBER analysis.
    """
    bits = np.asarray(bits, dtype=np.int8)

    if not np.all(np.isin(bits, [0, 1])):
        raise ValueError(
            "bits must contain only 0 or 1."
        )

    _validate_probability(
        noise_probability,
        "noise_probability",
    )

    noisy_bits = bits.copy()

    error_events = (
        rng.random(bits.size) < noise_probability
    )

    noisy_bits[error_events] = 1 - noisy_bits[error_events]

    return noisy_bits


def transmit_through_channel(
    bits: np.ndarray,
    bases: np.ndarray,
    loss_probability: float,
    noise_probability: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Transmit BB84 states through the simplified quantum channel.

    The channel applies:

        1. Loss
        2. Noise to surviving signals

    Parameters
    ----------
    bits:
        Bit values encoded by Alice.

    bases:
        Preparation bases selected by Alice.

    loss_probability:
        Probability of losing a signal.

    noise_probability:
        Probability of introducing a bit-flip error.

    rng:
        NumPy random number generator.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        surviving_bits:
            Bit values of signals that reached Bob.

        surviving_bases:
            Preparation bases associated with surviving signals.

        surviving_mask:
            Boolean mask identifying which original signals survived.

    Notes
    -----
    Loss is applied before noise.

    Noise is applied only to signals that survive the channel.

    The preparation basis is not changed by this simplified noise model.
    """
    bits = np.asarray(bits, dtype=np.int8)
    bases = np.asarray(bases, dtype=np.int8)

    if bits.shape != bases.shape:
        raise ValueError(
            "bits and bases must have the same shape."
        )

    if not np.all(np.isin(bits, [0, 1])):
        raise ValueError(
            "bits must contain only 0 or 1."
        )

    if not np.all(np.isin(bases, [0, 1])):
        raise ValueError(
            "bases must contain only 0 or 1."
        )

    surviving_mask = apply_channel_loss(
        n_signals=bits.size,
        loss_probability=loss_probability,
        rng=rng,
    )

    surviving_bits = bits[surviving_mask]
    surviving_bases = bases[surviving_mask]

    surviving_bits = apply_channel_noise(
        bits=surviving_bits,
        noise_probability=noise_probability,
        rng=rng,
    )

    return (
        surviving_bits,
        surviving_bases,
        surviving_mask,
    )