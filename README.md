# Hemolysis Icterus Lipemia Agent

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Hemolysis Icterus Lipemia Agent** is an advanced analytical and computational platform implementing Spectrophotometric HIL-Index Interference Arbiter.

HIL (Hemolysis, Icterus, Lipemia) Index Interpreter.

Interprets spectrophotometric interference indices and determines
their impact on clinical analyte results.

HIL Index values (semi-quantitative, 0-100+ scale):
  Hemolysis (H-index):
    Normal: 0-49, Mild: 50-100, Moderate: 100-250, Severe: >250
  Icterus (I-index):
    Normal: 0-19, Mild: 20-40, Moderate: 40-60, Severe: >60
  Lipemia (L-index):
    Normal: 0-99, Mild: 100-200, Moderate: 200-500, Severe: >500

Affected analytes by HIL interference:
  Hemolysis affects: K+, LDH, AST, ALT, bilirubin, haptoglobin, troponin
  Icterus affects: creatinine (Jaffe), triglycerides, uric acid
  Lipemia affects: sodium (indirect), triglycerides, total protein, amylase

Decision: Accept, flag, or reject for each analyte based on HIL level.

Zero-dependency Python stdlib implementation.
Author: Dr. Abu Suraih Sakhri
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`CorrectionResult`**: Result of an analyte correction computation.
- **`HILCorrectionEngine`**: Applies published correction formulas to analyte values when HIL indices
indicate pre-analytical interference.
- **`HILReading`**: A single HIL index reading with collection metadata.
- **`SiteShiftStatistics`**: Statistical summary for a site/shift combination.
- **`TrendReport`**: Aggregated trend report for HIL indices.
- **`HILTrendTracker`**: Tracks and analyzes HIL index trends by collection site and phlebotomy shift
to identify systemic pre-analytical issues.

---

## 📐 Mathematical Formulation & Logic

```text
  Applies published correction formulas to provide corrected analyte values when
  correction_formula: str
  "formula_type": "linear_subtraction",
  "formula_type": "flag_only",
  Applies published correction formulas to analyte values when HIL indices
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --hemolysis <value> --icterus <value> --lipemia <value> --analyte <value>
```

### Parameter Reference
- `--hemolysis`: Specifies input measurement or parameter value.
- `--icterus`: Specifies input measurement or parameter value.
- `--lipemia`: Specifies input measurement or parameter value.
- `--analyte`: Specifies input measurement or parameter value.
- `--analytes`: Specifies input measurement or parameter value.
- `--input`: Specifies input measurement or parameter value.
- `--output`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `case_id` | Parameter / observation metric | Required |
| `patient_synthetic_id` | Parameter / observation metric | Required |
| `metric_primary` | Parameter / observation metric | Required |
| `metric_secondary` | Parameter / observation metric | Required |
| `is_stat` | Parameter / observation metric | Required |
| `status_flag` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t hemolysis-icterus-lipemia-agent .
docker run -p 8000:8000 hemolysis-icterus-lipemia-agent
```
