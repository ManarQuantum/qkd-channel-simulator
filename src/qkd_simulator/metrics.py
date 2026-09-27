"""
Performance and security metrics for the QKD simulator.

This module provides functions for calculating:

- Detection/survival rate
- Sifted-key fraction
- QBER
- Binary entropy
- Simplified asymptotic BB84 secret-key fraction
- Simplified secret-key rate per transmitted signal
- Security-status interpretation

The security model used here is intentionally simplified. It is useful
for studying trends and performance, but it is not a finite-key security
proof or a complete implementation of practical QKD security analysis.
"""

from __future__ import annotations

import numpy as np


# ---------------------------------------------------------------------------
# Security-model constants
# ---------------------------------------------------------------------------

DEFAULT_QBER_THRESHOLD = 0.11


# ---------------------------------------------------------------------------
# Basic communication metrics
# ---------------------------------------------------------------------------

def calculate_detection_rate(
    surviving_mask: np.ndarray,
) -> float:
    """
    Calculate the fraction of transmitted signals that survived the channel.

    Parameters
    ----------
    surviving_mask:
        Boolean array where True indicates that a signal reached Bob.

    Returns
    -------
    float
        Detection/survival rate in the interval [0, 1].

    Notes
    -----
    In this simplified simulator, "detection rate" refers to the fraction
    of transmitted signals that survive the modeled channel loss.

    It does not represent a detailed detector-efficiency model.
    """
    surviving_mask = np.asarray(surviving_mask, dtype=bool)

    if surviving_mask.size == 0:
        return 0.0

    return float(np.mean(surviving_mask))


def calculate_sifted_key_fraction(
    sifted_key_length: int,
    n_transmitted: int,
) -> float:
    """
    Calculate the fraction of transmitted signals contributing to the
    sifted key.

    Parameters
    ----------
    sifted_key_length:
        Number of bits remaining after basis sifting.

    n_transmitted:
        Total number of signals originally transmitted by Alice.

    Returns
    -------
    float
        Sifted-key fraction per transmitted signal.
    """
    if n_transmitted <= 0:
        raise ValueError(
            "n_transmitted must be greater than zero."
        )

    if sifted_key_length < 0:
        raise ValueError(
            "sifted_key_length cannot be negative."
        )

    if sifted_key_length > n_transmitted:
        raise ValueError(
            "sifted_key_length cannot exceed n_transmitted."
        )

    return sifted_key_length / n_transmitted


# ---------------------------------------------------------------------------
# QBER
# ---------------------------------------------------------------------------

def calculate_qber(
    alice_key: np.ndarray,
    bob_key: np.ndarray,
) -> float:
    """
    Calculate the Quantum Bit Error Rate (QBER).

    QBER is defined as:

        QBER = number of mismatched sifted bits
               --------------------------------
               number of compared sifted bits

    Parameters
    ----------
    alice_key:
        Alice's sifted key.

    bob_key:
        Bob's sifted key.

    Returns
    -------
    float
        QBER in the interval [0, 1].

    Notes
    -----
    An empty sifted key returns 0.0 because there are no bits on which
    to estimate an error rate. The caller should separately track the
    sifted-key length when interpreting this situation.
    """
    alice_key = np.asarray(alice_key, dtype=np.int8)
    bob_key = np.asarray(bob_key, dtype=np.int8)

    if alice_key.shape != bob_key.shape:
        raise ValueError(
            "alice_key and bob_key must have the same shape."
        )

    if alice_key.size == 0:
        return 0.0

    if not np.all(np.isin(alice_key, [0, 1])):
        raise ValueError(
            "alice_key must contain only 0 or 1."
        )

    if not np.all(np.isin(bob_key, [0, 1])):
        raise ValueError(
            "bob_key must contain only 0 or 1."
        )

    errors = np.count_nonzero(alice_key != bob_key)

    return float(errors / alice_key.size)


# ---------------------------------------------------------------------------
# Binary entropy
# ---------------------------------------------------------------------------

def binary_entropy(qber: float) -> float:
    """
    Calculate the binary entropy h_2(q).

    The binary entropy is:

        h_2(q) = -q log2(q) - (1-q) log2(1-q)

    with the conventional definitions:

        0 log2(0) = 0

    Parameters
    ----------
    qber:
        Error probability q in the interval [0, 1].

    Returns
    -------
    float
        Binary entropy in bits.
    """
    if not 0.0 <= qber <= 1.0:
        raise ValueError(
            "qber must be between 0 and 1."
        )

    if qber == 0.0 or qber == 1.0:
        return 0.0

    return float(
        -qber * np.log2(qber)
        - (1.0 - qber) * np.log2(1.0 - qber)
    )


# ---------------------------------------------------------------------------
# Secret-key model
# ---------------------------------------------------------------------------

def calculate_secret_key_fraction(
    qber: float,
) -> float:
    """
    Calculate the simplified asymptotic BB84 secret-key fraction.

    The model used is:

        r = max(0, 1 - 2 h_2(Q))

    where:

        r  = estimated secret bits per sifted bit
        Q  = QBER
        h2 = binary entropy

    This corresponds to an idealized asymptotic BB84 model with
    one-way reconciliation under simplified assumptions.

    Parameters
    ----------
    qber:
        Quantum Bit Error Rate.

    Returns
    -------
    float
        Estimated secret-key fraction per sifted bit.

    Important
    ---------
    This is not a finite-key security proof. Practical systems require
    additional considerations such as finite-size effects, parameter
    estimation, error-correction efficiency, privacy amplification,
    device imperfections, and implementation-specific security models.
    """
    entropy = binary_entropy(qber)

    secret_fraction = 1.0 - 2.0 * entropy

    return float(max(0.0, secret_fraction))


def calculate_secret_key_rate(
    qber: float,
    sifted_key_fraction: float,
) -> float:
    """
    Calculate the estimated secret-key rate per transmitted signal.

    The model is:

        R = q * [1 - 2 h_2(Q)]

    where:

        q = sifted-key fraction per transmitted signal
        Q = QBER

    Negative values are clipped to zero because a negative secret-key
    rate is interpreted as no extractable secret key under this model.

    Parameters
    ----------
    qber:
        Quantum Bit Error Rate.

    sifted_key_fraction:
        Fraction of transmitted signals contributing to the sifted key.

    Returns
    -------
    float
        Estimated secret bits per transmitted signal.
    """
    if not 0.0 <= sifted_key_fraction <= 1.0:
        raise ValueError(
            "sifted_key_fraction must be between 0 and 1."
        )

    secret_fraction = calculate_secret_key_fraction(qber)

    return float(
        sifted_key_fraction * secret_fraction
    )


# ---------------------------------------------------------------------------
# Security interpretation
# ---------------------------------------------------------------------------

def classify_security_status(
    qber: float,
    threshold: float = DEFAULT_QBER_THRESHOLD,
) -> str:
    """
    Provide a simplified interpretation of the observed QBER.

    Parameters
    ----------
    qber:
        Measured QBER.

    threshold:
        QBER threshold used by this simplified model.

    Returns
    -------
    str
        One of:

        "potentially_secure"
        "abort"

    Notes
    -----
    The default threshold is approximately 11%, corresponding to the
    point where the idealized asymptotic expression

        1 - 2 h_2(Q)

    approaches zero.

    This threshold must NOT be interpreted as a universal security
    threshold for all practical QKD systems.
    """
    if not 0.0 <= qber <= 1.0:
        raise ValueError(
            "qber must be between 0 and 1."
        )

    if not 0.0 < threshold < 1.0:
        raise ValueError(
            "threshold must be between 0 and 1."
        )

    if qber < threshold:
        return "potentially_secure"

    return "abort"