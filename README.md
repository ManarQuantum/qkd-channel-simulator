# QKD Channel & Security Simulator

A small research-oriented simulator for studying how **channel noise, channel loss, and intercept-resend eavesdropping** affect the performance of a simplified BB84 quantum key distribution (QKD) link.

The project focuses on the relationship between physical/channel conditions and measurable QKD performance metrics such as **QBER, sifted-key fraction, detection rate, and estimated secret-key rate**.

---

## Research Question

> **How do channel noise, channel loss, and Eve's intervention probability affect QBER, secret-key generation, and the security of a QKD link?**

Rather than implementing BB84 as a quantum circuit, this project uses a **classical probabilistic representation of BB84 measurement statistics** to focus on communication-channel analysis and controlled experiments.

---

## Objectives

The simulator is designed to:

* Model the essential probabilistic behavior of BB84.
* Distinguish channel loss from channel errors.
* Model a simplified intercept-resend attack.
* Measure Quantum Bit Error Rate (QBER).
* Estimate secret-key generation performance.
* Investigate individual and combined channel impairments.
* Visualize the relationship between channel conditions and QKD performance.
* Provide a reproducible computational experiment suitable for further extension.

---

## Model

The communication process is represented as:

```text
Alice
  │
  ▼
Eve
  │
  ▼
Channel Loss
  │
  ▼
Channel Noise
  │
  ▼
Bob
  │
  ▼
Basis Reconciliation
  │
  ▼
Sifted Key
  │
  ▼
QBER / Secret-Key Analysis
```

### BB84 Representation

Each signal is represented by:

* A random bit: `0` or `1`.
* A randomly selected basis: `Z` or `X`.

Bob independently selects a measurement basis.

When Alice and Bob use the same basis, Bob obtains Alice's encoded bit in the ideal model.

When their bases differ, Bob's result is modeled as a random bit. These events are subsequently discarded during basis sifting.

### Channel Loss

Channel loss is represented by:

$$
p_{\mathrm{loss}} \in [0,1]
$$

Each signal survives with probability:

$$
1-p_{\mathrm{loss}}
$$

Lost signals do not contribute to the sifted key.

### Channel Noise

Channel noise is represented by:

$$
p_{\mathrm{noise}} \in [0,1]
$$

Each surviving signal has an independent probability $p_{\mathrm{noise}}$ of being flipped.

### Eve's Attack

Eve performs an intercept-resend attack with probability:

$$
p_{\mathrm{Eve}} \in [0,1]
$$

For an attacked signal, Eve:

1. Intercepts the signal.
2. Randomly selects a BB84 basis.
3. Measures the signal.
4. Resends a state corresponding to her measurement result.

For a complete intercept-resend attack, the expected BB84 QBER is approximately:

$$
Q \approx 0.25
$$

---

## Performance Metrics

### Detection Rate

The fraction of transmitted signals that survive channel loss:

$$
D =
\frac{N_{\mathrm{surviving}}}
{N_{\mathrm{transmitted}}}
$$

### Sifted-Key Fraction

The fraction of transmitted signals remaining after basis sifting:

$$
q =
\frac{N_{\mathrm{sifted}}}
{N_{\mathrm{transmitted}}}
$$

### Quantum Bit Error Rate

QBER measures disagreement between Alice's and Bob's sifted bits:

$$
Q =
\frac{N_{\mathrm{errors}}}
{N_{\mathrm{sifted}}}
$$

### Secret-Key Fraction

The project uses the simplified asymptotic BB84 model:

$$
r(Q) =
\max\left(0,\;1-2h_2(Q)\right)
$$

where the binary entropy is:

$$
h_2(Q)
=
-Q\log_2(Q)
-(1-Q)\log_2(1-Q)
$$

### Estimated Secret-Key Rate

The estimated secret-key rate per transmitted signal is:

$$
R = q\,r(Q)
$$

This provides an idealized performance estimate rather than a complete finite-key security analysis.

---

## Experiments

The notebook contains four main experiments.

### 1. Ideal Baseline

The first experiment establishes an ideal reference case:

$$
p_{\mathrm{noise}}
=
p_{\mathrm{loss}}
=
p_{\mathrm{Eve}}
=
0
$$

Expected behavior:

* Approximately all signals survive.
* QBER is close to zero.
* Approximately half of transmitted signals survive basis sifting.
* The estimated secret-key rate approaches the ideal sifted fraction.

### 2. Channel Noise

Channel noise is varied while loss and Eve are disabled.

The experiment investigates:

* QBER vs. noise probability.
* Secret-key rate vs. noise probability.
* Detection rate.
* Sifted-key fraction.

The expected result is that increasing noise increases QBER and reduces estimated secret-key performance.

### 3. Eve Intercept-Resend Attack

Eve's attack probability is varied while channel noise and loss are disabled.

The experiment investigates:

* QBER vs. Eve attack probability.
* Secret-key rate vs. Eve attack probability.
* Detection rate.
* Sifted-key fraction.

For a full intercept-resend attack:

$$
p_{\mathrm{Eve}} = 1
$$

the simulated QBER should approach:

$$
Q \approx 0.25
$$

This provides a basic validation of the eavesdropping model.

### 4. Combined Noise and Eve Study

A two-dimensional parameter sweep varies:

* Channel noise probability.
* Eve attack probability.

The resulting heatmaps visualize:

* QBER across the parameter space.
* Estimated secret-key rate across the parameter space.

This provides the main combined view of the simulator and demonstrates how multiple sources of disturbance can jointly reduce QKD performance.

---

## Main Results

The experiments illustrate three distinct effects:

| Condition            | Detection Rate          | QBER                    | Secret-Key Rate |
| -------------------- | ----------------------- | ----------------------- | --------------- |
| Channel noise        | Approximately unchanged | Increases               | Decreases       |
| Eve intercept-resend | Approximately unchanged | Increases               | Decreases       |
| Channel loss         | Decreases               | Approximately unchanged | Decreases       |

In simplified terms:

$$
\text{Loss}
\rightarrow
\text{fewer usable signals}
$$

$$
\text{Noise}
\rightarrow
\text{more bit errors}
$$

$$
\text{Eavesdropping}
\rightarrow
\text{additional detectable errors}
$$

This distinction is central to the project.

A low QBER does not necessarily imply a high key-generation rate because substantial channel loss can reduce the number of usable signals.

---

## Security Interpretation

For the experiments, a simplified QBER threshold is used:

$$
Q_{\mathrm{threshold}} = 0.11
$$

The simulator uses this threshold only as an experimental classification:

* $Q < Q_{\mathrm{threshold}}$ → `potentially_secure`
* $Q \geq Q_{\mathrm{threshold}}$ → `abort`

This threshold is part of the simplified model and should **not** be interpreted as a universal security boundary.

The simulator is not a finite-key security proof and does not establish security guarantees for practical QKD systems.

---

## Repository Structure

```text
qkd-channel-simulator/
│
├── README.md
├── requirements.txt
├── LICENSE
│
├── qkd_channel_simulator.ipynb
│
├── src/
│   └── qkd_simulator/
│       ├── __init__.py
│       ├── protocol.py
│       ├── channel.py
│       ├── attacks.py
│       ├── metrics.py
│       └── experiments.py
│
├── results/
│   ├── qber_vs_noise.png
│   ├── key_rate_vs_noise.png
│   ├── qber_vs_attack.png
│   ├── key_rate_vs_attack.png
│   ├── loss_vs_key_rate.png
│   └── security_heatmap.png
│
└── tests/
    └── test_simulator.py
```

The notebook provides the main reproducible experiment workflow, while the Python modules contain the underlying simulation and analysis functions.

---

## Technologies

* **Python**
* **NumPy** — numerical simulation and random sampling
* **Pandas** — experiment results and tabular analysis
* **Matplotlib** — visualization
* **Jupyter Notebook** — reproducible experiment environment

Qiskit is intentionally not required. The project focuses on probabilistic QKD performance analysis rather than quantum-circuit implementation.

---

## Running the Project

Clone the repository and enter the project directory:

```bash
git clone https://github.com/ManarQuantum/qkd-channel-simulator.git
cd qkd-channel-simulator
```

Create and activate a virtual environment.

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Launch Jupyter:

```bash
jupyter notebook
```

Open:

```text
qkd_channel_simulator.ipynb
```

and execute the notebook cells sequentially.

---

## Reproducibility

The experiments use explicit random seeds and defined simulation parameters so that results can be reproduced.

The number of transmitted signals and Monte Carlo trials can be adjusted to investigate statistical variability and computational cost.

Because the simulator is stochastic, small numerical differences can occur if the random seeds or simulation parameters are changed.

---

## Limitations

This project intentionally uses a compact model rather than attempting to reproduce a production-grade QKD system.

It does not currently model:

* Explicit quantum state vectors or density matrices.
* Optical propagation.
* Atmospheric turbulence.
* Distance-dependent attenuation.
* Detector dark counts.
* Detector inefficiency.
* Background photons.
* Polarization drift.
* Decoy-state BB84.
* Finite-key security analysis.
* Composable security.
* Arbitrary quantum attacks.
* Quantum memories.
* Quantum repeaters.
* Multi-node quantum networks.
* Network routing or resource allocation.

The secret-key-rate calculation is an idealized asymptotic estimate:

$$
R =
q\max\left(0,\;1-2h_2(Q)\right)
$$

and should therefore be interpreted as a performance-oriented estimate rather than a rigorous finite-key secret-key guarantee.

---

## Future Work

Possible extensions include:

* Finite-key statistical analysis.
* More realistic detector models.
* Distance-dependent channel loss.
* Atmospheric and free-space optical effects.
* Decoy-state BB84.
* Additional attack models.
* Explicit quantum-state simulation.
* Realistic satellite-to-ground channel models.
* Integration with QKD network simulations.
* Heterogeneous quantum-link modeling.

These extensions would connect the simplified QKD-link model to broader studies of realistic quantum communication systems and, eventually, quantum-network performance.

---

## Relation to Quantum Communication Research

This project focuses specifically on the **QKD/quantum communication layer** rather than attempting to model an entire quantum network.

It provides a small computational foundation for studying how physical communication conditions influence:

$$
\text{Channel Parameters}
\rightarrow
\text{QBER}
\rightarrow
\text{Secret-Key Performance}
$$

This relationship is relevant to more advanced research involving realistic photonic channels, satellite-to-ground quantum communication, heterogeneous quantum links, and quantum-network design.

---

## License

This project is released under the MIT License. See [`LICENSE`](LICENSE) for details.

---

## Author

**Amal Boumen**

Quantum Computing | Quantum Communication | Quantum Networking

Research interests include:

* Quantum Communication
* Quantum Key Distribution
* Quantum Networking
* Quantum Internet
* Quantum Optics
* Photonic Quantum Systems
