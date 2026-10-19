# 🛡️ PHANTOM SHIELD
### Spam & Phishing Email Detection Using Finite Automata

PHANTOM SHIELD is a Python-based spam and phishing email detection system developed as a **Theory of Computation (ToC) project**. It demonstrates how finite automata and formal language concepts can be applied to identify suspicious patterns in email messages.

The project implements **Nondeterministic Finite Automata (NFA)** for pattern matching and converts the NFA into a **Deterministic Finite Automaton (DFA)** using the subset construction algorithm. Both approaches can be used to analyze email text and compare their detection results through an interactive web interface.

## ✨ Features

- **Spam & Phishing Detection:** Scans email text for predefined suspicious keywords and phrases.
- **NFA Pattern Matching:** Demonstrates nondeterministic finite automata-based pattern recognition.
- **NFA-to-DFA Conversion:** Implements subset construction to convert an NFA into an equivalent DFA.
- **Automata Visualization:** Displays automata-related information and transition structures where supported by the application.
- **Step-by-Step Execution:** Provides execution traces to help understand how patterns are processed.
- **Transition Table:** Presents state transitions for examining automata behavior.
- **Email Scanner Interface:** Allows users to enter email text and inspect the detection result.
- **Benchmarking:** Compares the execution performance of NFA and DFA implementations.
- **Dataset Testing:** Supports testing multiple email samples against expected detection outcomes.

## 🎯 Project Objectives

1. Apply Theory of Computation concepts to a practical text-analysis problem.
2. Implement pattern matching using Nondeterministic Finite Automata.
3. Convert an NFA into an equivalent DFA using subset construction.
4. Compare the behavior and execution performance of NFA and DFA implementations.
5. Build an interactive interface to demonstrate the concepts and results.

## 🧠 Theory of Computation Concepts

### 1. Nondeterministic Finite Automaton (NFA)

An NFA is a finite-state machine that can have multiple possible transitions for an input symbol. In this project, the NFA is used to recognize predefined suspicious patterns in email text.

### 2. Deterministic Finite Automaton (DFA)

A DFA has exactly one defined transition for each state and input symbol in its alphabet. The DFA implementation processes the same patterns using deterministic state transitions.

### 3. Subset Construction

Subset construction converts an NFA into an equivalent DFA by representing sets of NFA states as individual DFA states. This enables a comparison between the two automata while preserving the recognized language.

### 4. Pattern Matching

The detector checks email content against a predefined collection of suspicious keywords and phrases, such as:

- `free`
- `win`
- `click here`
- `urgent`
- `verify your account`

These patterns are used for demonstration and academic evaluation.

## ⚙️ Technology Stack

- **Programming Language:** Python
- **Web Framework:** Flask
- **Frontend:** HTML, CSS, JavaScript
- **Core Concepts:** NFA, DFA, subset construction, finite-state pattern matching
- **Testing & Evaluation:** Automated tests, sample email dataset, execution benchmarking
- **Development Environment:** Visual Studio Code

## 🏗️ System Workflow

1. The user enters an email message or selects a sample for testing.
2. The application processes the email using the implemented NFA and DFA detectors.
3. Suspicious patterns are checked against the predefined rules.
4. The application displays the detection results and relevant execution details.
5. The results from the two approaches can be compared.
6. Benchmarking and dataset testing help evaluate the implementations.

## 🚀 Getting Started

### Prerequisites

- Python 3 installed
- Git installed
- A code editor such as Visual Studio Code

### Installation

Clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/PHANTOM-SHIELD.git
```

Navigate to the project directory:

```bash
cd PHANTOM-SHIELD
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the project's dependencies using the dependency file provided in the repository. If the project contains `requirements.txt`, run:

```bash
pip install -r requirements.txt
```

### Run the Application

Follow the project's included startup instructions. If the repository contains `run_windows.bat`, you can launch it from PowerShell using:

```powershell
.\run_windows.bat
```

Open the local URL displayed by Flask in your browser.

## 🧪 Testing

The project includes tests and sample-data evaluation for checking the implementation.

Run the test command specified in the project's documentation. If it uses pytest, run:

```bash
pytest
```

Test results and benchmark values may vary by environment. Refer to the included test files and project documentation for the exact coverage and execution procedure.

## 📊 Evaluation

The project can be evaluated using:

- NFA and DFA detection-result comparison
- Correct recognition of predefined suspicious patterns
- Sample dataset classification results
- State-transition and execution traces
- NFA-to-DFA subset construction
- Execution-time benchmarking

## ⚠️ Limitations

PHANTOM SHIELD is an educational, rule-based prototype. It does not use a trained machine-learning model or guarantee the identification of every spam or phishing email.

Its results depend on the predefined patterns and matching rules. Legitimate emails may contain suspicious keywords, and malicious emails may avoid them. The application should not be treated as a production-grade email security solution.

---

*PHANTOM SHIELD — Exploring how finite automata can help recognize suspicious email patterns.*
