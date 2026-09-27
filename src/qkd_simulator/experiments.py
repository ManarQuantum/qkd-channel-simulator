"""
Experiment utilities for the QKD channel simulator.

This module combines the protocol, channel, attack, and metric layers
into complete simulation runs and parameter sweeps.

The functions here are designed to be called from the Jupyter notebook
without duplicating simulation logic.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .attacks import intercept_resend
from .channel import apply_channel_loss, apply_channel_noise
from .metrics import (
    calculate_detection_rate,
    calculate_qber,
    calculate_secret_key_fraction,
    calculate_secret_key_rate,
    calculate_sifted_key_fraction,
)
from .protocol import (
    generate_random_bases,
    generate_random_bits,
    measure_states,
    prepare_states,
    sift_key,
)


# ---------------------------------------------------------------------------
# Single simulation
# ---------------------------------------------------------------------------

def simulate_bb84(
    n_signals: int = 10_000,
    noise_probability: float = 0.0,
    loss_probability: float = 0.0,
    attack_probability: float = 0.0,
    seed: int | None = None,
) -> dict:
    """
    Run one complete BB84 simulation.

    Simulation pipeline:

        Alice
          ↓
        State preparation
          ↓
        Eve intercept-resend
          ↓
        Channel loss
          ↓
        Channel noise
          ↓
        Bob measurement
          ↓
        Basis sifting
          ↓
        Metrics

    Parameters
    ----------
    n_signals:
        Number of BB84 signals transmitted by Alice.

    noise_probability:
        Probability of a channel-induced bit-flip error.

    loss_probability:
        Probability that a signal is lost before reaching Bob.

    attack_probability:
        Probability that Eve intercepts an individual signal.

    seed:
        Random seed for reproducibility.

    Returns
    -------
    dict
        Dictionary containing simulation parameters, intermediate
        quantities, and final performance metrics.
    """
    if n_signals <= 0:
        raise ValueError(
            "n_signals must be greater than zero."
        )

    if not 0.0 <= noise_probability <= 1.0:
        raise ValueError(
            "noise_probability must be between 0 and 1."
        )

    if not 0.0 <= loss_probability <= 1.0:
        raise ValueError(
            "loss_probability must be between 0 and 1."
        )

    if not 0.0 <= attack_probability <= 1.0:
        raise ValueError(
            "attack_probability must be between 0 and 1."
        )

    rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # 1. Alice generates random bits and bases
    # ------------------------------------------------------------------

    alice_bits = generate_random_bits(
        n_signals=n_signals,
        rng=rng,
    )

    alice_bases = generate_random_bases(
        n_signals=n_signals,
        rng=rng,
    )

    # Represent Alice's BB84 states.
    state_bits, state_bases = prepare_states(
        bits=alice_bits,
        bases=alice_bases,
    )

    # ------------------------------------------------------------------
    # 2. Eve may intercept and resend
    # ------------------------------------------------------------------

    (
        forwarded_bits,
        forwarded_bases,
        attacked_mask,
    ) = intercept_resend(
        state_bits=state_bits,
        state_bases=state_bases,
        attack_probability=attack_probability,
        rng=rng,
    )

    # ------------------------------------------------------------------
    # 3. Channel loss
    # ------------------------------------------------------------------

    surviving_mask = apply_channel_loss(
        n_signals=n_signals,
        loss_probability=loss_probability,
        rng=rng,
    )

    surviving_bits = forwarded_bits[surviving_mask]
    surviving_bases = forwarded_bases[surviving_mask]

    # ------------------------------------------------------------------
    # 4. Channel noise
    # ------------------------------------------------------------------

    noisy_bits = apply_channel_noise(
        bits=surviving_bits,
        noise_probability=noise_probability,
        rng=rng,
    )

    # ------------------------------------------------------------------
    # 5. Bob randomly chooses measurement bases
    # ------------------------------------------------------------------

    n_surviving = noisy_bits.size

    bob_bases = generate_random_bases(
        n_signals=n_surviving,
        rng=rng,
    )

    # ------------------------------------------------------------------
    # 6. Bob measures the received states
    # ------------------------------------------------------------------

    bob_bits = measure_states(
        state_bits=noisy_bits,
        state_bases=surviving_bases,
        measurement_bases=bob_bases,
        rng=rng,
    )

    # ------------------------------------------------------------------
    # 7. Basis sifting
    # ------------------------------------------------------------------

    alice_surviving_bits = alice_bits[surviving_mask]
    alice_surviving_bases = alice_bases[surviving_mask]

    (
        sifted_alice_key,
        sifted_bob_key,
    ) = sift_key(
        alice_bits=alice_surviving_bits,
        alice_bases=alice_surviving_bases,
        bob_bits=bob_bits,
        bob_bases=bob_bases,
    )

    # ------------------------------------------------------------------
    # 8. Calculate metrics
    # ------------------------------------------------------------------

    detection_rate = calculate_detection_rate(
        surviving_mask=surviving_mask,
    )

    sifted_key_length = sifted_alice_key.size

    sifted_key_fraction = calculate_sifted_key_fraction(
        sifted_key_length=sifted_key_length,
        n_transmitted=n_signals,
    )

    qber = calculate_qber(
        alice_key=sifted_alice_key,
        bob_key=sifted_bob_key,
    )

    secret_key_fraction = calculate_secret_key_fraction(
        qber=qber,
    )

    secret_key_rate = calculate_secret_key_rate(
        qber=qber,
        sifted_key_fraction=sifted_key_fraction,
    )

    return {
        # Simulation parameters
        "n_signals": n_signals,
        "noise_probability": noise_probability,
        "loss_probability": loss_probability,
        "attack_probability": attack_probability,
        "seed": seed,

        # Signal counts
        "n_surviving": n_surviving,
        "n_lost": n_signals - n_surviving,
        "n_attacked": int(np.count_nonzero(attacked_mask)),
        "sifted_key_length": sifted_key_length,

        # Performance metrics
        "detection_rate": detection_rate,
        "sifted_key_fraction": sifted_key_fraction,
        "qber": qber,
        "secret_key_fraction": secret_key_fraction,
        "secret_key_rate": secret_key_rate,
    }


# ---------------------------------------------------------------------------
# Repeated simulations
# ---------------------------------------------------------------------------

def run_trials(
    n_trials: int = 10,
    n_signals: int = 10_000,
    noise_probability: float = 0.0,
    loss_probability: float = 0.0,
    attack_probability: float = 0.0,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Run repeated simulations under identical channel conditions.

    Each trial receives a different deterministic random seed derived
    from the supplied base seed.

    Parameters
    ----------
    n_trials:
        Number of independent Monte Carlo trials.

    n_signals:
        Number of signals per trial.

    noise_probability:
        Channel noise probability.

    loss_probability:
        Channel loss probability.

    attack_probability:
        Eve's attack probability.

    seed:
        Base random seed.

    Returns
    -------
    pandas.DataFrame
        One row per simulation trial.
    """
    if n_trials <= 0:
        raise ValueError(
            "n_trials must be greater than zero."
        )

    results = []

    for trial in range(n_trials):
        trial_seed = seed + trial

        result = simulate_bb84(
            n_signals=n_signals,
            noise_probability=noise_probability,
            loss_probability=loss_probability,
            attack_probability=attack_probability,
            seed=trial_seed,
        )

        result["trial"] = trial

        results.append(result)

    return pd.DataFrame(results)


# ---------------------------------------------------------------------------
# Noise sweep
# ---------------------------------------------------------------------------

def run_noise_sweep(
    noise_values: np.ndarray | list[float],
    n_signals: int = 10_000,
    n_trials: int = 10,
    loss_probability: float = 0.0,
    attack_probability: float = 0.0,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Sweep over channel-noise probabilities.

    Parameters
    ----------
    noise_values:
        Noise probabilities to investigate.

    n_signals:
        Number of signals per trial.

    n_trials:
        Number of repeated simulations per noise value.

    loss_probability:
        Fixed channel loss probability.

    attack_probability:
        Fixed Eve attack probability.

    seed:
        Base random seed.

    Returns
    -------
    pandas.DataFrame
        Mean and standard deviation of key metrics for each noise level.
    """
    rows = []

    for index, noise_probability in enumerate(noise_values):
        trials = run_trials(
            n_trials=n_trials,
            n_signals=n_signals,
            noise_probability=float(noise_probability),
            loss_probability=loss_probability,
            attack_probability=attack_probability,
            seed=seed + index * n_trials,
        )

        rows.append(
            {
                "noise_probability": float(noise_probability),
                "qber_mean": trials["qber"].mean(),
                "qber_std": trials["qber"].std(ddof=1),
                "secret_key_rate_mean": (
                    trials["secret_key_rate"].mean()
                ),
                "secret_key_rate_std": (
                    trials["secret_key_rate"].std(ddof=1)
                ),
                "detection_rate_mean": (
                    trials["detection_rate"].mean()
                ),
                "sifted_key_fraction_mean": (
                    trials["sifted_key_fraction"].mean()
                ),
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Eve attack sweep
# ---------------------------------------------------------------------------

def run_attack_sweep(
    attack_values: np.ndarray | list[float],
    n_signals: int = 10_000,
    n_trials: int = 10,
    noise_probability: float = 0.0,
    loss_probability: float = 0.0,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Sweep over Eve's intercept-resend attack probability.

    Parameters
    ----------
    attack_values:
        Eve attack probabilities to investigate.

    n_signals:
        Number of signals per trial.

    n_trials:
        Number of repeated simulations per attack probability.

    noise_probability:
        Fixed channel noise probability.

    loss_probability:
        Fixed channel loss probability.

    seed:
        Base random seed.

    Returns
    -------
    pandas.DataFrame
        Mean and standard deviation of key metrics for each attack level.
    """
    rows = []

    for index, attack_probability in enumerate(attack_values):
        trials = run_trials(
            n_trials=n_trials,
            n_signals=n_signals,
            noise_probability=noise_probability,
            loss_probability=loss_probability,
            attack_probability=float(attack_probability),
            seed=seed + index * n_trials,
        )

        rows.append(
            {
                "attack_probability": float(attack_probability),
                "qber_mean": trials["qber"].mean(),
                "qber_std": trials["qber"].std(ddof=1),
                "secret_key_rate_mean": (
                    trials["secret_key_rate"].mean()
                ),
                "secret_key_rate_std": (
                    trials["secret_key_rate"].std(ddof=1)
                ),
                "detection_rate_mean": (
                    trials["detection_rate"].mean()
                ),
                "sifted_key_fraction_mean": (
                    trials["sifted_key_fraction"].mean()
                ),
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Loss sweep
# ---------------------------------------------------------------------------

def run_loss_sweep(
    loss_values: np.ndarray | list[float],
    n_signals: int = 10_000,
    n_trials: int = 10,
    noise_probability: float = 0.0,
    attack_probability: float = 0.0,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Sweep over channel-loss probabilities.

    Parameters
    ----------
    loss_values:
        Loss probabilities to investigate.

    n_signals:
        Number of signals per trial.

    n_trials:
        Number of repeated simulations per loss probability.

    noise_probability:
        Fixed channel noise probability.

    attack_probability:
        Fixed Eve attack probability.

    seed:
        Base random seed.

    Returns
    -------
    pandas.DataFrame
        Mean and standard deviation of key metrics for each loss level.
    """
    rows = []

    for index, loss_probability in enumerate(loss_values):
        trials = run_trials(
            n_trials=n_trials,
            n_signals=n_signals,
            noise_probability=noise_probability,
            loss_probability=float(loss_probability),
            attack_probability=attack_probability,
            seed=seed + index * n_trials,
        )

        rows.append(
            {
                "loss_probability": float(loss_probability),
                "detection_rate_mean": (
                    trials["detection_rate"].mean()
                ),
                "detection_rate_std": (
                    trials["detection_rate"].std(ddof=1)
                ),
                "sifted_key_fraction_mean": (
                    trials["sifted_key_fraction"].mean()
                ),
                "sifted_key_fraction_std": (
                    trials["sifted_key_fraction"].std(ddof=1)
                ),
                "qber_mean": trials["qber"].mean(),
                "qber_std": trials["qber"].std(ddof=1),
                "secret_key_rate_mean": (
                    trials["secret_key_rate"].mean()
                ),
                "secret_key_rate_std": (
                    trials["secret_key_rate"].std(ddof=1)
                ),
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Two-dimensional noise + Eve sweep
# ---------------------------------------------------------------------------

def run_noise_attack_sweep(
    noise_values: np.ndarray | list[float],
    attack_values: np.ndarray | list[float],
    n_signals: int = 10_000,
    n_trials: int = 5,
    loss_probability: float = 0.0,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Run a two-dimensional parameter sweep over noise and Eve attack rate.

    Parameters
    ----------
    noise_values:
        Channel noise probabilities.

    attack_values:
        Eve attack probabilities.

    n_signals:
        Number of signals per trial.

    n_trials:
        Number of repeated simulations for every parameter combination.

    loss_probability:
        Fixed channel loss probability.

    seed:
        Base random seed.

    Returns
    -------
    pandas.DataFrame
        One row per noise/attack parameter combination.

    Notes
    -----
    This function is intended to generate the main heatmap of the project.
    """
    rows = []
    combination_index = 0

    for noise_probability in noise_values:
        for attack_probability in attack_values:
            trials = run_trials(
                n_trials=n_trials,
                n_signals=n_signals,
                noise_probability=float(noise_probability),
                loss_probability=loss_probability,
                attack_probability=float(attack_probability),
                seed=seed + combination_index * n_trials,
            )

            rows.append(
                {
                    "noise_probability": float(
                        noise_probability
                    ),
                    "attack_probability": float(
                        attack_probability
                    ),
                    "qber_mean": trials["qber"].mean(),
                    "qber_std": trials["qber"].std(ddof=1),
                    "secret_key_rate_mean": (
                        trials["secret_key_rate"].mean()
                    ),
                    "secret_key_rate_std": (
                        trials["secret_key_rate"].std(ddof=1)
                    ),
                    "detection_rate_mean": (
                        trials["detection_rate"].mean()
                    ),
                    "sifted_key_fraction_mean": (
                        trials["sifted_key_fraction"].mean()
                    ),
                }
            )

            combination_index += 1

    return pd.DataFrame(rows)