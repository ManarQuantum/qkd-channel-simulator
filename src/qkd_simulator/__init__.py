"""
QKD Channel & Security Simulator.

A simplified research-oriented simulator for studying how channel noise,
channel loss, and intercept-resend eavesdropping affect BB84 performance.

Public API
----------
The main functions exposed by this package are:

- simulate_bb84
- run_trials
- run_noise_sweep
- run_attack_sweep
- run_loss_sweep
- run_noise_attack_sweep

Metrics are also exposed for direct analysis.
"""

from .experiments import (
    run_attack_sweep,
    run_loss_sweep,
    run_noise_attack_sweep,
    run_noise_sweep,
    run_trials,
    simulate_bb84,
)

from .metrics import (
    DEFAULT_QBER_THRESHOLD,
    binary_entropy,
    calculate_detection_rate,
    calculate_qber,
    calculate_secret_key_fraction,
    calculate_secret_key_rate,
    calculate_sifted_key_fraction,
    classify_security_status,
)

from .protocol import (
    X_BASIS,
    Z_BASIS,
    generate_random_bases,
    generate_random_bits,
    measure_states,
    prepare_states,
    sift_key,
)

__all__ = [
    # Main simulation
    "simulate_bb84",
    "run_trials",

    # Experiments
    "run_noise_sweep",
    "run_attack_sweep",
    "run_loss_sweep",
    "run_noise_attack_sweep",

    # Metrics
    "calculate_detection_rate",
    "calculate_sifted_key_fraction",
    "calculate_qber",
    "binary_entropy",
    "calculate_secret_key_fraction",
    "calculate_secret_key_rate",
    "classify_security_status",
    "DEFAULT_QBER_THRESHOLD",

    # Protocol
    "Z_BASIS",
    "X_BASIS",
    "generate_random_bits",
    "generate_random_bases",
    "prepare_states",
    "measure_states",
    "sift_key",
]