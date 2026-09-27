import sys
from pathlib import Path
import unittest

import numpy as np


# Make the src/ package importable when tests are run from the repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from qkd_simulator.protocol import (
    Z_BASIS,
    X_BASIS,
    generate_random_bits,
    generate_random_bases,
    prepare_states,
    measure_states,
    sift_key,
)

from qkd_simulator.channel import (
    apply_channel_loss,
    apply_channel_noise,
    transmit_through_channel,
)

from qkd_simulator.attacks import intercept_resend

from qkd_simulator.metrics import (
    calculate_detection_rate,
    calculate_sifted_key_fraction,
    calculate_qber,
    binary_entropy,
    calculate_secret_key_fraction,
    calculate_secret_key_rate,
    classify_security_status,
)

from qkd_simulator.experiments import (
    simulate_bb84,
    run_noise_sweep,
)


class TestProtocol(unittest.TestCase):
    """Tests for the simplified BB84 protocol layer."""

    def test_random_bits_have_correct_shape_and_values(self):
        rng = np.random.default_rng(1)

        bits = generate_random_bits(1000, rng)

        self.assertEqual(len(bits), 1000)
        self.assertTrue(np.all((bits == 0) | (bits == 1)))

    def test_random_bases_have_correct_shape_and_values(self):
        rng = np.random.default_rng(2)

        bases = generate_random_bases(1000, rng)

        self.assertEqual(len(bases), 1000)
        self.assertTrue(np.all((bases == Z_BASIS) | (bases == X_BASIS)))

    def test_prepare_states_preserves_bits_and_bases(self):
        bits = np.array([0, 1, 1, 0])
        bases = np.array([Z_BASIS, X_BASIS, Z_BASIS, X_BASIS])

        state_bits, state_bases = prepare_states(bits, bases)

        np.testing.assert_array_equal(state_bits, bits)
        np.testing.assert_array_equal(state_bases, bases)

    def test_same_basis_measurement_is_deterministic(self):
        rng = np.random.default_rng(3)

        bits = np.array([0, 1, 0, 1] * 2500)
        bases = np.array([Z_BASIS, X_BASIS] * 5000)

        measured = measure_states(
            state_bits=bits,
            state_bases=bases,
            measurement_bases=bases,
            rng=rng,
        )

        np.testing.assert_array_equal(measured, bits)

    def test_different_basis_measurement_is_random(self):
        rng = np.random.default_rng(4)

        n_signals = 20000

        bits = generate_random_bits(n_signals, rng)
        state_bases = np.full(n_signals, Z_BASIS)
        measurement_bases = np.full(n_signals, X_BASIS)

        measured = measure_states(
            state_bits=bits,
            state_bases=state_bases,
            measurement_bases=measurement_bases,
            rng=rng,
        )

        proportion_of_ones = np.mean(measured)

        # Measurement in the wrong BB84 basis should produce
        # approximately random results.
        self.assertAlmostEqual(proportion_of_ones, 0.5, delta=0.03)

    def test_sifting_keeps_only_matching_bases(self):
        alice_bits = np.array([0, 1, 0, 1, 1])
        alice_bases = np.array([Z_BASIS, X_BASIS, Z_BASIS, X_BASIS, Z_BASIS])

        bob_bits = np.array([0, 0, 1, 1, 1])
        bob_bases = np.array([Z_BASIS, Z_BASIS, X_BASIS, X_BASIS, Z_BASIS])

        alice_key, bob_key = sift_key(
            alice_bits,
            alice_bases,
            bob_bits,
            bob_bases,
        )

        np.testing.assert_array_equal(alice_key, np.array([0, 1, 1]))
        np.testing.assert_array_equal(bob_key, np.array([0, 1, 1]))


class TestChannel(unittest.TestCase):
    """Tests for channel loss and noise."""

    def test_zero_loss_keeps_all_signals(self):
        rng = np.random.default_rng(10)

        mask = apply_channel_loss(
            n_signals=1000,
            loss_probability=0.0,
            rng=rng,
        )

        self.assertTrue(np.all(mask))

    def test_full_loss_removes_all_signals(self):
        rng = np.random.default_rng(11)

        mask = apply_channel_loss(
            n_signals=1000,
            loss_probability=1.0,
            rng=rng,
        )

        self.assertFalse(np.any(mask))

    def test_loss_probability_is_statistically_correct(self):
        rng = np.random.default_rng(12)

        n_signals = 20000
        loss_probability = 0.30

        mask = apply_channel_loss(
            n_signals=n_signals,
            loss_probability=loss_probability,
            rng=rng,
        )

        detection_rate = np.mean(mask)

        self.assertAlmostEqual(
            detection_rate,
            1.0 - loss_probability,
            delta=0.02,
        )

    def test_zero_noise_does_not_change_bits(self):
        rng = np.random.default_rng(13)

        bits = generate_random_bits(10000, rng)

        noisy_bits = apply_channel_noise(
            bits,
            noise_probability=0.0,
            rng=rng,
        )

        np.testing.assert_array_equal(noisy_bits, bits)

    def test_full_noise_flips_all_bits(self):
        rng = np.random.default_rng(14)

        bits = generate_random_bits(10000, rng)

        noisy_bits = apply_channel_noise(
            bits,
            noise_probability=1.0,
            rng=rng,
        )

        np.testing.assert_array_equal(noisy_bits, 1 - bits)

    def test_noise_probability_is_statistically_correct(self):
        rng = np.random.default_rng(15)

        bits = generate_random_bits(20000, rng)

        noisy_bits = apply_channel_noise(
            bits,
            noise_probability=0.10,
            rng=rng,
        )

        error_rate = np.mean(noisy_bits != bits)

        self.assertAlmostEqual(
            error_rate,
            0.10,
            delta=0.02,
        )

    def test_transmit_through_channel(self):
        rng = np.random.default_rng(16)

        bits = generate_random_bits(10000, rng)
        bases = generate_random_bases(10000, rng)

        transmitted_bits, transmitted_bases, survival_mask = (
            transmit_through_channel(
                bits=bits,
                bases=bases,
                loss_probability=0.20,
                noise_probability=0.10,
                rng=rng,
            )
        )

        self.assertEqual(len(transmitted_bits), np.sum(survival_mask))
        self.assertEqual(len(transmitted_bases), np.sum(survival_mask))


class TestAttack(unittest.TestCase):
    """Tests for the simplified intercept-resend attack."""

    def test_zero_attack_probability_changes_nothing(self):
        rng = np.random.default_rng(20)

        bits = generate_random_bits(1000, rng)
        bases = generate_random_bases(1000, rng)

        forwarded_bits, forwarded_bases, attacked_mask = intercept_resend(
            state_bits=bits,
            state_bases=bases,
            attack_probability=0.0,
            rng=rng,
        )

        np.testing.assert_array_equal(forwarded_bits, bits)
        np.testing.assert_array_equal(forwarded_bases, bases)
        self.assertFalse(np.any(attacked_mask))

    def test_full_attack_probability_attacks_every_signal(self):
        rng = np.random.default_rng(21)

        bits = generate_random_bits(1000, rng)
        bases = generate_random_bases(1000, rng)

        _, _, attacked_mask = intercept_resend(
            state_bits=bits,
            state_bases=bases,
            attack_probability=1.0,
            rng=rng,
        )

        self.assertTrue(np.all(attacked_mask))

    def test_full_intercept_resend_produces_expected_qber(self):
        """
        A full intercept-resend attack should produce approximately
        25% QBER on the sifted key in ideal BB84.
        """
        result = simulate_bb84(
            n_signals=20000,
            noise_probability=0.0,
            loss_probability=0.0,
            attack_probability=1.0,
            seed=22,
        )

        self.assertAlmostEqual(
            result["qber"],
            0.25,
            delta=0.03,
        )


class TestMetrics(unittest.TestCase):
    """Tests for QKD performance and security metrics."""

    def test_detection_rate(self):
        mask = np.array([True, True, True, False, False])

        detection_rate = calculate_detection_rate(mask)

        self.assertAlmostEqual(detection_rate, 0.6)

    def test_sifted_key_fraction(self):
        fraction = calculate_sifted_key_fraction(
            sifted_key_length=500,
            n_transmitted=1000,
        )

        self.assertAlmostEqual(fraction, 0.5)

    def test_zero_qber(self):
        alice_key = np.array([0, 1, 1, 0, 1])
        bob_key = np.array([0, 1, 1, 0, 1])

        qber = calculate_qber(alice_key, bob_key)

        self.assertEqual(qber, 0.0)

    def test_known_qber(self):
        alice_key = np.array([0, 1, 1, 0, 1])
        bob_key = np.array([0, 0, 1, 1, 1])

        qber = calculate_qber(alice_key, bob_key)

        self.assertAlmostEqual(qber, 0.4)

    def test_binary_entropy(self):
        self.assertAlmostEqual(binary_entropy(0.0), 0.0)
        self.assertAlmostEqual(binary_entropy(1.0), 0.0)
        self.assertAlmostEqual(binary_entropy(0.5), 1.0)

    def test_secret_key_fraction_at_zero_qber(self):
        fraction = calculate_secret_key_fraction(0.0)

        self.assertAlmostEqual(fraction, 1.0)

    def test_secret_key_fraction_at_high_qber(self):
        fraction = calculate_secret_key_fraction(0.12)

        self.assertEqual(fraction, 0.0)

    def test_secret_key_rate(self):
        rate = calculate_secret_key_rate(
            qber=0.0,
            sifted_key_fraction=0.5,
        )

        self.assertAlmostEqual(rate, 0.5)

    def test_security_classification(self):
        self.assertEqual(
            classify_security_status(0.05),
            "potentially_secure",
        )

        self.assertEqual(
            classify_security_status(0.11),
            "abort",
        )

        self.assertEqual(
            classify_security_status(0.20),
            "abort",
        )


class TestSimulation(unittest.TestCase):
    """End-to-end tests for the complete QKD simulation."""

    def test_ideal_bb84_baseline(self):
        result = simulate_bb84(
            n_signals=20000,
            noise_probability=0.0,
            loss_probability=0.0,
            attack_probability=0.0,
            seed=30,
        )

        self.assertEqual(result["n_surviving"], 20000)
        self.assertEqual(result["n_lost"], 0)

        self.assertAlmostEqual(
            result["detection_rate"],
            1.0,
        )

        self.assertAlmostEqual(
            result["qber"],
            0.0,
        )

        # Approximately half the signals should survive basis sifting.
        self.assertAlmostEqual(
            result["sifted_key_fraction"],
            0.5,
            delta=0.03,
        )

        # With zero QBER, the simplified secret-key rate
        # equals the sifted-key fraction.
        self.assertAlmostEqual(
            result["secret_key_rate"],
            result["sifted_key_fraction"],
        )

    def test_noise_increases_qber(self):
        result = simulate_bb84(
            n_signals=20000,
            noise_probability=0.10,
            loss_probability=0.0,
            attack_probability=0.0,
            seed=31,
        )

        self.assertAlmostEqual(
            result["qber"],
            0.10,
            delta=0.03,
        )

        self.assertAlmostEqual(
            result["detection_rate"],
            1.0,
        )

    def test_loss_reduces_detection_and_key_rate(self):
        result = simulate_bb84(
            n_signals=20000,
            noise_probability=0.0,
            loss_probability=0.30,
            attack_probability=0.0,
            seed=32,
        )

        self.assertAlmostEqual(
            result["detection_rate"],
            0.70,
            delta=0.03,
        )

        self.assertAlmostEqual(
            result["qber"],
            0.0,
        )

        # With zero noise, loss should reduce the number of
        # usable signals without introducing QBER.
        self.assertLess(
            result["secret_key_rate"],
            0.5,
        )

    def test_high_noise_removes_secret_key(self):
        result = simulate_bb84(
            n_signals=20000,
            noise_probability=0.20,
            loss_probability=0.0,
            attack_probability=0.0,
            seed=33,
        )

        self.assertGreater(
            result["qber"],
            0.15,
        )

        self.assertEqual(
            result["secret_key_rate"],
            0.0,
        )

    def test_full_attack_removes_secret_key(self):
        result = simulate_bb84(
            n_signals=20000,
            noise_probability=0.0,
            loss_probability=0.0,
            attack_probability=1.0,
            seed=34,
        )

        self.assertGreater(
            result["qber"],
            0.20,
        )

        self.assertEqual(
            result["secret_key_rate"],
            0.0,
        )

    def test_noise_sweep_returns_expected_rows(self):
        noise_values = [0.0, 0.05, 0.10]

        results = run_noise_sweep(
            noise_values=noise_values,
            n_signals=2000,
            n_trials=2,
            seed=40,
        )

        self.assertEqual(
            len(results),
            len(noise_values),
        )

        np.testing.assert_array_equal(
            results["noise_probability"].to_numpy(),
            np.array(noise_values),
        )

        expected_columns = {
            "noise_probability",
            "qber_mean",
            "qber_std",
            "secret_key_rate_mean",
            "secret_key_rate_std",
            "detection_rate_mean",
            "sifted_key_fraction_mean",
        }

        self.assertTrue(
            expected_columns.issubset(results.columns)
        )


if __name__ == "__main__":
    unittest.main()