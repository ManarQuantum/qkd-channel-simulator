# QKD Channel & Security Simulator

A lightweight research-oriented simulator for studying how **channel noise, channel loss, and eavesdropping** affect the performance and security of a simplified BB84 quantum key distribution (QKD) link.

The project focuses on the relationship between physical channel conditions and key-generation performance through measurable quantities such as **detection rate, sifted-key fraction, QBER, and estimated secret-key rate**.

---

## Research Question

**How do channel noise, channel loss, and Eve's intercept-resend intervention probability affect QBER, secret-key generation, and the security of a QKD link?**

The simulator separates three different effects:

* **Loss:** signals disappear before measurement.
* **Noise:** surviving signals may be corrupted.
* **Eavesdropping:** Eve intercepts and resends quantum states, introducing detectable errors.

This allows their effects to be studied independently and in combination.

---

## Objectives

The main objectives are to:

1. Simulate a simplified BB84 communication link.
2. Model probabilistic channel loss.
3. Model independent channel bit errors.
4. Model Eve's intercept-resend attack.
5. Calculate the Quantum Bit Error Rate (QBER).
6. Estimate the secret-key fraction and secret-key rate.
7. Study how different channel conditions affect QKD performance.
8. Visualize the relationship between noise, eavesdropping, and key generation.
9. Provide a reproducible simulation framework that can later be extended toward more realistic quantum communication models.

---

## System Model

The simulated communication pipeline is:

```text
Alice
  │
  │ Random bits + random bases
  ▼
State Preparation
  │
  ▼
Eve: Intercept-Resend
  │
  ▼
Channel Loss
  │
  ▼
Channel Noise
  │
  ▼
Bob: Measurement
  │
  ▼
Basis Reconciliation
  │
  ▼
Sifted Key
  │
  ├── QBER
  ├── Secret-Key Fraction
  └── Estimated Secret-Key Rate
```

The simulator uses a classical probabilistic representation of BB84 states rather than a full quantum-state simulator. This keeps the model lightweight while allowing the effects of channel imperfections and eavesdropping to be studied quantitatively.

---

## BB84 Representation

Each signal is represented using:

* A random classical bit:

$$
b \in \{0,1\}
$$

* A randomly selected BB84 basis:

$$
B \in \{Z,X\}
$$

Alice prepares a state according to her bit and basis.

Bob independently chooses a measurement basis.

If Alice and Bob use the same basis, Bob obtains Alice's bit deterministically in the ideal case.

If they use different bases, Bob obtains a random bit.

After transmission and measurement, Alice and Bob publicly compare their basis choices and keep only the signals for which their bases matched.

---

## Channel Loss

Channel loss represents signals that fail to reach Bob.

The loss probability is:

$$
p_{\mathrm{loss}} \in [0,1]
$$

The corresponding survival probability is:

$$
P_{\mathrm{survival}} = 1-p_{\mathrm{loss}}
$$

Lost signals are removed from the data before Bob's measurement and therefore do not contribute to the sifted key or QBER.

This distinction is important: **loss reduces the quantity of usable key material, but does not directly introduce errors into surviving signals.**

---

## Channel Noise

Channel noise represents independent bit errors affecting signals that survive transmission.

The noise probability is:

$$
p_{\mathrm{noise}} \in [0,1]
$$

For each surviving signal, its bit may be flipped according to this probability.

Noise therefore affects the **quality** of the resulting key by increasing the QBER.

Unlike loss, noisy signals remain present and can contribute to the sifted key.

---

## Eve's Intercept-Resend Attack

The simulator models a simplified intercept-resend attack.

Eve attacks each signal with probability:

$$
p_{\mathrm{Eve}} \in [0,1]
$$

For an attacked signal:

1. Eve randomly selects a measurement basis.
2. Eve measures the incoming state.
3. Eve prepares a new state using her measurement result and chosen basis.
4. The resent state continues toward Bob.

Because Eve does not know Alice's basis in advance, her intervention introduces errors when Bob later measures in the correct basis.

For a full intercept-resend attack:

$$
p_{\mathrm{Eve}} = 1
$$

the expected QBER on the sifted key approaches approximately:

$$
Q \approx 0.25
$$

This provides a useful reference for studying the statistical detectability of eavesdropping.

---

## Performance and Security Metrics

### Detection Rate

The detection rate measures the fraction of transmitted signals that survive the channel:

$$
D =
\frac{N_{\mathrm{surviving}}}
{N_{\mathrm{transmitted}}}
$$

For the simplified loss model:

$$
D \approx 1-p_{\mathrm{loss}}
$$

---

### Sifted-Key Fraction

The sifted-key fraction is the number of sifted signals relative to the total number transmitted:

$$
q =
\frac{N_{\mathrm{sifted}}}
{N_{\mathrm{transmitted}}}
$$

In an ideal BB84 link without loss, the expected sifted fraction approaches:

$$
q \approx 0.5
$$

because Alice and Bob independently choose between two bases.

With channel loss, the expected sifted fraction becomes approximately:

$$
q \approx 0.5(1-p_{\mathrm{loss}})
$$

---

### Quantum Bit Error Rate

The Quantum Bit Error Rate (QBER) measures the fraction of errors among the sifted bits:

$$
Q =
\frac{N_{\mathrm{errors}}}
{N_{\mathrm{sifted}}}
$$

Here, an error means that Alice's and Bob's sifted key bits disagree.

A low QBER indicates that the sifted key contains relatively few observed errors, while a high QBER indicates stronger channel disturbance or possible eavesdropping.

---

### Binary Entropy

The binary entropy function is:

$$
h_2(Q)
=
-Q\log_2(Q)
-(1-Q)\log_2(1-Q)
$$

Binary entropy quantifies the uncertainty associated with a binary variable having error probability $Q$.

---

### Estimated Secret-Key Fraction

The simulator uses the simplified asymptotic expression:

$$
r(Q)
=
\max\left(0,1-2h_2(Q)\right)
$$

where $r(Q)$ represents the estimated secret-key fraction per sifted bit.

If the estimated secret-key fraction becomes zero, the simulated channel conditions do not provide a positive key rate under this simplified model.

This is an idealized asymptotic model and **not a finite-key security proof**.

---

### Estimated Secret-Key Rate

The estimated secret-key rate per transmitted signal is:

$$
R = q\,r(Q)
$$

This combines both:

* the quantity of signals that survive basis reconciliation, represented by $q$;
* the estimated amount of secure key obtainable from those sifted bits, represented by $r(Q)$.

The result is therefore an idealized performance estimate rather than a complete finite-key security analysis.

---

## Security Interpretation

For visualization and experiment classification, the simulator uses a reference QBER threshold of:

$$
Q_{\mathrm{threshold}} = 0.11
$$

The simplified classification is:

* $Q < Q_{\mathrm{threshold}}$: `potentially_secure`
* $Q \geq Q_{\mathrm{threshold}}$: `abort`

This threshold is used as a **reference within the simplified simulation model**. It should not be interpreted as a universal security guarantee for real QKD systems.

Real QKD security depends on the protocol details, finite-key effects, error correction, privacy amplification, device assumptions, implementation imperfections, and the specific security proof being used.

---

## Experiments

The notebook contains four main experiments.

### 1. Ideal Baseline

The first experiment establishes an ideal reference case:

$$
p_{\mathrm{noise}} = 0
$$

$$
p_{\mathrm{loss}} = 0
$$

$$
p_{\mathrm{Eve}} = 0
$$

In this case:

* all signals survive;
* no additional bit errors are introduced;
* QBER should remain close to zero;
* approximately half of the transmitted signals should contribute to the sifted key;
* the estimated secret-key rate should approach its ideal value.

The simulation uses repeated trials to account for statistical fluctuations.

---

### 2. Channel Noise Sweep

The noise experiment varies the channel noise probability while keeping channel loss and Eve's intervention probability at zero.

$$
p_{\mathrm{noise}} \in [0,0.20]
$$

The experiment measures:

* QBER versus noise probability;
* estimated secret-key rate versus noise probability.

The expected behavior is that increasing noise increases QBER and decreases the estimated secret-key rate.

The detection rate should remain approximately constant because the noise model does not remove signals.

Generated figures:

```text
results/qber_vs_noise.png
results/key_rate_vs_noise.png
```

---

### 3. Eve Intercept-Resend Sweep

The attack experiment varies Eve's intervention probability while keeping channel loss and noise at zero.

$$
p_{\mathrm{Eve}} \in [0,1]
$$

The experiment measures:

* QBER versus Eve's attack probability;
* estimated secret-key rate versus Eve's attack probability.

For a full intercept-resend attack:

$$
p_{\mathrm{Eve}} = 1
$$

the simulated QBER should approach:

$$
Q \approx 0.25
$$

The experiment also compares the simulation with the expected approximate relationship:

$$
Q \approx 0.25p_{\mathrm{Eve}}
$$

for the ideal no-noise, no-loss case.

Generated figures:

```text
results/qber_vs_attack.png
results/key_rate_vs_attack.png
```

---

### 4. Channel Loss Sweep

The loss experiment varies the channel loss probability while keeping noise and Eve's intervention probability at zero.

$$
p_{\mathrm{loss}} \in [0,0.90]
$$

The experiment measures:

* detection rate;
* sifted-key fraction;
* QBER;
* estimated secret-key rate.

The expected detection rate is approximately:

$$
D \approx 1-p_{\mathrm{loss}}
$$

and the expected sifted-key fraction is approximately:

$$
q \approx 0.5(1-p_{\mathrm{loss}})
$$

Because the loss model removes signals without corrupting surviving bits, QBER should remain close to zero.

The estimated secret-key rate decreases as channel loss increases because fewer signals remain available for key generation.

Generated figure:

```text
results/loss_vs_key_rate.png
```

---

## Combined Noise and Eavesdropping Experiment

The simulator also studies the combined effect of channel noise and Eve's intervention.

The experiment varies both:

$$
p_{\mathrm{noise}} \in [0,0.20]
$$

and:

$$
p_{\mathrm{Eve}} \in [0,1]
$$

The resulting QBER and estimated secret-key rate are visualized using heatmaps.

This experiment illustrates how multiple sources of disturbance can interact and reduce the operating margin of the QKD link.

Importantly, the combined QBER is not simply the sum of the independent QBER contributions because errors introduced by different mechanisms can sometimes cancel.

For the simplified model, an approximate combined error probability can be written as:

$$
Q
\approx
0.25p_{\mathrm{Eve}}
+
p_{\mathrm{noise}}
-
0.5p_{\mathrm{Eve}}p_{\mathrm{noise}}
$$

The simulation itself is used to capture the resulting behavior through Monte Carlo trials.

Generated figure:

```text
results/security_heatmap.png
```

---

## Main Results

The expected qualitative behavior of the three main channel conditions is:

| Condition                  |          Detection Rate |                    QBER | Estimated Secret-Key Rate |
| -------------------------- | ----------------------: | ----------------------: | ------------------------: |
| Ideal                      |                    High |                  Near 0 |                      High |
| Increased Noise            | Approximately unchanged |               Increases |                 Decreases |
| Increased Eve Intervention | Approximately unchanged |               Increases |                 Decreases |
| Increased Loss             |               Decreases | Approximately unchanged |                 Decreases |

This highlights an important distinction:

**Loss primarily affects how much key material survives, while noise and eavesdropping primarily affect the quality and security of the surviving key material.**

---

## Monte Carlo Simulation

Because the simulator uses random bit, basis, channel, and attack choices, individual simulation runs naturally fluctuate.

The experiments therefore use repeated Monte Carlo trials.

The main simulations use:

```text
Signals per trial: 10,000
Number of trials: 10
```

The combined noise-versus-Eve experiment uses multiple independent trials for each parameter combination.

Results are summarized using means and standard deviations where appropriate.

Fixed random seeds are used in the notebook to make the experiments reproducible.

---

## Repository Structure

```text
qkd-channel-simulator/
├── README.md
├── requirements.txt
├── LICENSE
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

---

## Technologies

The project uses:

* **Python**
* **NumPy**
* **Pandas**
* **Matplotlib**
* **Jupyter Notebook**
* **unittest**

Qiskit is intentionally **not required** for this project.

The purpose of this simulator is to study channel behavior and QKD performance using a lightweight probabilistic model rather than to reproduce a quantum circuit implementation.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/ManarQuantum/qkd-channel-simulator.git
cd qkd-channel-simulator
```

Create a virtual environment:

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

---

## Running the Notebook

Start Jupyter:

```bash
jupyter notebook
```

Then open:

```text
qkd_channel_simulator.ipynb
```

Run the notebook from beginning to end to reproduce the experiments and generate the figures in the `results/` directory.

---

## Running the Tests

The project includes unit and end-to-end tests for the protocol, channel, attack, metrics, and experiment components.

Run:

```bash
python -m unittest discover -s tests -v
```

The tests cover:

* random bit and basis generation;
* BB84 state preparation;
* measurement behavior;
* basis sifting;
* channel loss;
* channel noise;
* intercept-resend attacks;
* QBER calculation;
* binary entropy;
* secret-key fraction;
* secret-key rate;
* security classification;
* end-to-end simulation behavior;
* parameter sweeps.

---

## Reproducibility

The simulations use explicit random-number generators and fixed seeds in the notebook experiments.

This allows the reported results and visualizations to be reproduced while still preserving the stochastic nature of the model.

Changing the random seed will produce slightly different numerical results because the simulator is based on Monte Carlo sampling.

Increasing the number of signals or trials generally reduces statistical fluctuations.

---

## Limitations

This project is intentionally a simplified research model and does not attempt to provide a complete physical or security simulation of a real QKD system.

### Simplified quantum representation

BB84 states are represented using classical bit-and-basis information rather than explicit quantum state vectors, density matrices, or quantum optical states.

### Simplified channel model

The channel uses independent probabilistic loss and bit-flip noise.

It does not model detailed optical propagation, atmospheric turbulence, polarization drift, photon statistics, detector characteristics, or hardware imperfections.

### Simplified eavesdropping model

Only an intercept-resend attack is considered.

The simulator does not model more sophisticated collective, coherent, side-channel, or device-specific attacks.

### Asymptotic key-rate model

The secret-key expression is an idealized asymptotic estimate.

The project does not implement:

* finite-key analysis;
* composable security;
* realistic error-correction leakage;
* privacy-amplification protocols;
* decoy-state analysis;
* rigorous security proofs.

### Single-link model

The simulator represents a single Alice-to-Bob QKD link.

It does not model:

* quantum repeaters;
* quantum memories;
* entanglement distribution;
* network routing;
* resource allocation;
* multi-hop quantum networks;
* satellite constellation architectures.

These limitations are intentional so that the project can focus clearly on the relationship between channel conditions, QBER, and key-generation performance.

---

## Future Extensions

The simulator provides a foundation for more realistic quantum communication research.

Possible future extensions include:

* finite-key effects;
* realistic error-correction leakage;
* privacy amplification;
* decoy-state BB84;
* photon loss models;
* detector dark counts;
* detector efficiency;
* atmospheric turbulence;
* free-space optical channel models;
* fiber attenuation;
* polarization errors;
* realistic photon statistics;
* quantum-state or density-matrix simulations;
* satellite-to-ground QKD channels;
* time-dependent channel conditions;
* integration with quantum-network simulators.

These extensions could connect the current simplified QKD model to broader research in **quantum communication, satellite QKD, quantum networking, and the Quantum Internet**.

---

## Relation to Quantum Communication Research

This project focuses on the physical and statistical layer of a QKD communication link.

The central relationship studied is:

$$
\text{Channel Conditions}
\rightarrow
\text{QBER}
\rightarrow
\text{Secret-Key Fraction}
\rightarrow
\text{Key Generation Performance}
$$

Understanding this relationship is relevant to the design and evaluation of larger quantum communication systems, where physical link quality influences higher-level decisions such as link selection, routing, resource allocation, and network reliability.

The project therefore serves as a compact foundation for future work involving **physics-aware quantum network design and optimization**.

---

## License

This project is released under the MIT License.

See [LICENSE](LICENSE) for details.

---

## Author

**Amal Boumen**

Research interests:

* Quantum Communication
* Quantum Networking
* Quantum Internet
* Quantum Key Distribution
* Satellite Quantum Communication
* Quantum Optics
* Photonic Quantum Systems
