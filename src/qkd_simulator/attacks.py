"""
Eavesdropping models for the QKD simulator.

This module contains simplified attack models against the BB84 protocol.

Currently implemented:
    - Intercept-resend attack

The purpose is to study how Eve's intervention affects the observed QBER
and estimated secret-key performance.

This is a simplified educational model and is not intended to represent
a complete treatment of quantum attacks.
"""

from __future__ import annotations

import numpy as np

from .protocol import (
    generate_random_bases,
    measure_states,
    Z_BASIS,
    X_BASIS,
)


def _validate_probability(
    probability: float,
    name: str,
) -> None:
    """Validate that a probability lies in [0, 1]."""
    if not 0.0 <= probability <= 1.0:
        raise ValueError(
            f"{name} must be between 0 and 1."
        )


def intercept_resend(
    state_bits: np.ndarray,
    state_bases: np.ndarray,
    attack_probability: float,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Apply a simplified intercept-resend attack.

    For each transmitted state:

    1. With probability `attack_probability`, Eve intercepts the state.
    2. Eve randomly selects the Z or X basis.
    3. Eve measures the state using that basis.
    4. Eve prepares a new BB84 state corresponding to her measurement.
    5. The state is forwarded to Bob.

    If Eve does not attack a signal, the original state passes through
    unchanged.

    Parameters
    ----------
    state_bits:
        Bit values encoded by Alice.

    state_bases:
        Preparation bases selected by Alice.

    attack_probability:
        Probability that Eve intercepts an individual signal.

    rng:
        NumPy random number generator.

    Returns
    -------
    tuple[np.ndarray, np.ndarray, np.ndarray]
        forwarded_bits:
            Bit values of the states forwarded toward Bob.

        forwarded_bases:
            Preparation bases of the forwarded states.

        attacked_mask:
            Boolean array indicating which signals were intercepted.

    Notes
    -----
    When Eve measures in the same basis as Alice, she obtains the correct
    bit and can resend the same state.

    When Eve measures in the opposite basis, her result is random.
    She then resends a state in her measurement basis. If Bob later
    measures in Alice's original basis, this can introduce a detectable
    error.

    For ideal BB84 with Eve attacking every signal using a uniformly
    random basis, the expected QBER contribution on the sifted key is
    approximately 25%.
    """
    state_bits = np.asarray(state_bits, dtype=np.int8)
    state_bases = np.asarray(state_bases, dtype=np.int8)

    if state_bits.shape != state_bases.shape:
        raise ValueError(
            "state_bits and state_bases must have the same shape."
        )

    if not np.all(np.isin(state_bits, [0, 1])):
        raise ValueError(
            "state_bits must contain only 0 or 1."
        )

    if not np.all(np.isin(state_bases, [Z_BASIS, X_BASIS])):
        raise ValueError(
            "state_bases must contain only valid BB84 bases."
        )

    _validate_probability(
        attack_probability,
        "attack_probability",
    )

    n_signals = state_bits.size

    # Decide independently whether Eve attacks each signal.
    attacked_mask = (
        rng.random(n_signals) < attack_probability
    )

    # By default, Eve forwards the original states unchanged.
    forwarded_bits = state_bits.copy()
    forwarded_bases = state_bases.copy()

    n_attacked = np.count_nonzero(attacked_mask)

    if n_attacked == 0:
        return (
            forwarded_bits,
            forwarded_bases,
            attacked_mask,
        )

    # Eve randomly chooses a BB84 basis for every attacked signal.
    eve_bases = generate_random_bases(
        n_attacked,
        rng,
    )

    # Eve measures the intercepted states.
    eve_bits = measure_states(
        state_bits=state_bits[attacked_mask],
        state_bases=state_bases[attacked_mask],
        measurement_bases=eve_bases,
        rng=rng,
    )

    # Eve resends a state encoded according to her measurement.
    forwarded_bits[attacked_mask] = eve_bits
    forwarded_bases[attacked_mask] = eve_bases

    return (
        forwarded_bits,
        forwarded_bases,
        attacked_mask,
    )