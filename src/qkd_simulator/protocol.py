"""
BB84 protocol primitives.

This module contains the protocol-level operations used by the QKD simulator:

- Random bit generation
- Random basis generation
- BB84 state representation
- Measurement according to the BB84 measurement rules
- Sifting

The simulator uses a classical probabilistic representation of BB84 states
rather than constructing a quantum circuit for every transmitted signal.

A state is represented by:
    bit  : 0 or 1
    basis: 0 (computational/Z) or 1 (Hadamard/X)

This is sufficient for studying the statistical behavior of BB84 under
channel imperfections and intercept-resend attacks.
"""

from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# Basis conventions
# ---------------------------------------------------------------------------

Z_BASIS = 0
X_BASIS = 1


def generate_random_bits(
    n_signals: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Generate random binary values for Alice.

    Parameters
    ----------
    n_signals:
        Number of quantum signals to generate.
    rng:
        NumPy random number generator used for reproducibility.

    Returns
    -------
    np.ndarray
        Array containing 0/1 values.

    Raises
    ------
    ValueError
        If n_signals is not positive.
    """
    if n_signals <= 0:
        raise ValueError("n_signals must be greater than zero.")

    return rng.integers(0, 2, size=n_signals, dtype=np.int8)


def generate_random_bases(
    n_signals: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Generate random BB84 measurement/preparation bases.

    Basis convention:
        0 -> computational (Z) basis
        1 -> Hadamard (X) basis

    Parameters
    ----------
    n_signals:
        Number of bases to generate.
    rng:
        NumPy random number generator.

    Returns
    -------
    np.ndarray
        Array containing 0/1 basis values.
    """
    if n_signals <= 0:
        raise ValueError("n_signals must be greater than zero.")

    return rng.integers(0, 2, size=n_signals, dtype=np.int8)


def prepare_states(
    bits: np.ndarray,
    bases: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Represent Alice's BB84 states.

    In this simulator, an individual BB84 state is completely described by
    Alice's classical bit and preparation basis.

    Parameters
    ----------
    bits:
        Alice's binary values.
    bases:
        Alice's preparation bases.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Copies of the state bits and state bases.

    Raises
    ------
    ValueError
        If the arrays have different lengths or invalid values.
    """
    bits = np.asarray(bits, dtype=np.int8)
    bases = np.asarray(bases, dtype=np.int8)

    if bits.shape != bases.shape:
        raise ValueError("bits and bases must have the same shape.")

    if not np.all(np.isin(bits, [0, 1])):
        raise ValueError("bits must contain only 0 or 1.")

    if not np.all(np.isin(bases, [Z_BASIS, X_BASIS])):
        raise ValueError("bases must contain only Z_BASIS (0) or X_BASIS (1).")

    return bits.copy(), bases.copy()


def measure_states(
    state_bits: np.ndarray,
    state_bases: np.ndarray,
    measurement_bases: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """
    Measure BB84 states using Bob's selected bases.

    BB84 measurement rule:

    - If Bob measures in the same basis used for preparation, he obtains
      Alice's encoded bit deterministically.
    - If Bob measures in the opposite basis, the result is uniformly random.

    Parameters
    ----------
    state_bits:
        Encoded bit values of the states reaching Bob.
    state_bases:
        Preparation basis of each state.
    measurement_bases:
        Bob's measurement basis for each state.
    rng:
        NumPy random number generator.

    Returns
    -------
    np.ndarray
        Bob's measurement results.

    Raises
    ------
    ValueError
        If arrays have incompatible shapes or invalid values.
    """
    state_bits = np.asarray(state_bits, dtype=np.int8)
    state_bases = np.asarray(state_bases, dtype=np.int8)
    measurement_bases = np.asarray(measurement_bases, dtype=np.int8)

    if not (
        state_bits.shape
        == state_bases.shape
        == measurement_bases.shape
    ):
        raise ValueError(
            "state_bits, state_bases, and measurement_bases "
            "must have the same shape."
        )

    if not np.all(np.isin(state_bits, [0, 1])):
        raise ValueError("state_bits must contain only 0 or 1.")

    if not np.all(np.isin(state_bases, [Z_BASIS, X_BASIS])):
        raise ValueError("state_bases must contain only valid BB84 bases.")

    if not np.all(np.isin(measurement_bases, [Z_BASIS, X_BASIS])):
        raise ValueError(
            "measurement_bases must contain only valid BB84 bases."
        )

    results = np.empty_like(state_bits)

    same_basis = state_bases == measurement_bases
    different_basis = ~same_basis

    # Same basis -> deterministic measurement.
    results[same_basis] = state_bits[same_basis]

    # Different basis -> completely random measurement.
    n_random = np.count_nonzero(different_basis)

    if n_random > 0:
        results[different_basis] = rng.integers(
            0,
            2,
            size=n_random,
            dtype=np.int8,
        )

    return results


def sift_key(
    alice_bits: np.ndarray,
    alice_bases: np.ndarray,
    bob_bits: np.ndarray,
    bob_bases: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Perform BB84 basis sifting.

    Alice and Bob keep only the events for which they used the same basis.

    Parameters
    ----------
    alice_bits:
        Alice's original encoded bits.
    alice_bases:
        Alice's preparation bases.
    bob_bits:
        Bob's measurement results.
    bob_bases:
        Bob's measurement bases.

    Returns
    -------
    tuple[np.ndarray, np.ndarray]
        Sifted Alice key and sifted Bob key.

    Raises
    ------
    ValueError
        If input arrays have different shapes.
    """
    alice_bits = np.asarray(alice_bits, dtype=np.int8)
    alice_bases = np.asarray(alice_bases, dtype=np.int8)
    bob_bits = np.asarray(bob_bits, dtype=np.int8)
    bob_bases = np.asarray(bob_bases, dtype=np.int8)

    if not (
        alice_bits.shape
        == alice_bases.shape
        == bob_bits.shape
        == bob_bases.shape
    ):
        raise ValueError(
            "All input arrays must have the same shape."
        )

    matching_bases = alice_bases == bob_bases

    sifted_alice = alice_bits[matching_bases]
    sifted_bob = bob_bits[matching_bases]

    return sifted_alice, sifted_bob