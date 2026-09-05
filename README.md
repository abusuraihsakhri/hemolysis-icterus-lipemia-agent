# Hemolysis Icterus Lipemia Agent

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Reference Guidelines & Standards:** CLSI C56-A, CLSI EP28-A3, Westgard Multi-Rule QC, ISO 15189

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

**Hemolysis Icterus Lipemia Agent** is a clinical decision support platform implementing a Spectrophotometric HIL-Index Interference Arbiter.

Interprets spectrophotometric interference indices (Hemolysis, Icterus, Lipemia) and determines their impact on clinical analyte results.

### HIL Index Classifications

**Hemolysis (H-index):**
| Classification | Range |
|:---------------|:------|
| Normal | 0-49 |
| Mild | 50-100 |
| Moderate | 101-250 |
| Severe | >250 |

**Icterus (I-index):**
| Classification | Range |
|:---------------|:------|
| Normal | 0-19 |
| Mild | 20-40 |
| Moderate | 41-60 |
| Severe | >60 |

**Lipemia (L-index):**
| Classification | Range |
|:---------------|:------|
| Normal | 0-99 |
| Mild | 100-200 |
| Moderate | 201-500 |
| Severe | >500 |

### Affected Analytes

- **Hemolysis affects:** K+, LDH, AST, ALT, bilirubin, haptoglobin, troponin
- **Icterus affects:** creatinine (Jaffe), triglycerides, uric acid
- **Lipemia affects:** sodium (indirect), triglycerides, total protein, amylase

### Decision Logic

For each analyte, the system determines: **Accept**, **Flag**, or **Reject** based on HIL interference level.

---

## ⚙️ Key Modules

### Core HIL Engine (`hil_sentinel.py`)
- `classify_hil_index()` — Classifies HIL index values into severity levels
- `interpret_hil_indices()` — Interprets all three HIL indices with overall specimen quality
- `assess_analyte_impact()` — Assesses interference impact on specific analytes
- `assess_specimen()` — Complete specimen assessment with per-analyte decisions
- `process_batch()` — Batch CSV processing for multiple specimens

### HIL Correction Engine (`hil_correction_engine.py`)
- `HILCorrectionEngine` — Applies published correction formulas to analyte values
- Supports linear subtraction and flag-only correction types
- Covers K+, LDH, AST, ALT, troponin, bilirubin, creatinine, cholesterol, triglycerides, hemoglobin, sodium

### HIL Trend Tracker (`hil_trend_tracker.py`)
- `HILTrendTracker` — Tracks HIL index trends by collection site and phlebotomy shift
- Identifies systemic pre-analytical issues across collection locations
- Generates box plot data for visualization

### Specimen Quality Scorer (`specimen_quality_scorer.py`)
- `SpecimenQualityScorer` — Computes composite Specimen Quality Score (SQS)
- Factors: HIL interference, collection-to-centrifugation time, storage conditions
- Grades: EXCELLENT, GOOD, ACCEPTABLE, MARGINAL, REJECTED

### Enterprise Agent Suite (`agents/`)
- `PHIGuard` — Zero-PHI outbound interceptor with regex pattern detection
- `AuditTrail` / `AuditLogger` — HMAC-SHA256 tamper-evident audit trail
- `SystemSupervisor` — Multi-worker orchestration with consensus dossier generation
- `LLMFactory` — Air-gapped LLM adapter (Ollama, Claude, OpenAI, mock)

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/hemolysis-icterus-lipemia-agent.git
cd hemolysis-icterus-lipemia-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# For development (testing, FastAPI server)
pip install -e ".[dev]"
```

---

## 🚀 Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py interpret --hemolysis 150 --icterus 25 --lipemia 300
python cli.py analyte --analyte potassium --hemolysis 150
python cli.py specimen --hemolysis 150 --icterus 25 --lipemia 300
python cli.py list-analytes
```

### 3. Batch CSV Processing
```bash
python cli.py batch -i specimens.csv -o results.csv
```

### 4. HIL Correction Engine
```bash
python hil_correction_engine.py --analyte K --raw 6.8 --hil-type H --hil-value 20
python hil_correction_engine.py --list
```

### 5. HIL Trend Tracker
```bash
python hil_trend_tracker.py --input readings.csv --box-plot
python hil_trend_tracker.py --input readings.csv --period-start 2024-01-01 --period-end 2024-12-31
```

### 6. Specimen Quality Scorer
```bash
python specimen_quality_scorer.py --accession ACC-001 --hil-h 150 --collection-time "2024-01-15T08:30:00Z"
```

### 7. FastAPI REST Server
```bash
python -m hemolysis_icterus_lipemia_agent.cli serve --host 0.0.0.0 --port 8000
```

### 8. Enterprise Agent CLI
```bash
python -m hemolysis_icterus_lipemia_agent.cli audit --case-id CASE-001 --primary 26.2
python -m hemolysis_icterus_lipemia_agent.cli chat "system status"
python -m hemolysis_icterus_lipemia_agent.cli verify-audit
```

---

## 🛡️ Security Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Configurable Audit Secret:** Set `AUDIT_SECRET_KEY` environment variable for production deployments (generates ephemeral key with warning if unset).
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances, Claude, GPT-4o, and deterministic test mocks.

---

## 🧪 Testing

Run the complete test suite:

```bash
pytest -v
```

Run specific test modules:

```bash
pytest test_hil_sentinel.py -v          # Core HIL engine tests (46 tests)
pytest tests/test_enrichment.py -v      # Enrichment module tests
pytest tests/test_hemolysis_icterus_lipemia_agent.py -v  # Enterprise agent tests
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

### Docker
```bash
docker build -t hemolysis-icterus-lipemia-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key hemolysis-icterus-lipemia-agent
```

### Docker Compose
```bash
# Set your audit secret key
export AUDIT_SECRET_KEY=your-production-secret-key

docker-compose up -d
```

---

## 📁 Project Structure

```
hemolysis-icterus-lipemia-agent/
├── hil_sentinel.py                  # Core HIL index interpreter
├── hil_correction_engine.py         # Analyte correction formulas
├── hil_trend_tracker.py             # Site/shift trend analysis
├── specimen_quality_scorer.py       # Composite quality scoring
├── cli.py                           # Main CLI entry point
├── simulator.py                     # High-throughput simulation
├── enrichment.py                    # Enrichment feature suite
├── agents/                          # Enterprise agent framework
│   ├── base.py                      # PHI guard, audit trail
│   ├── models.py                    # Pydantic schemas
│   ├── supervisor.py                # Multi-worker orchestrator
│   ├── workers.py                   # Specialized QC workers
│   ├── api.py                       # FastAPI endpoints
│   ├── learning.py                  # Bayesian calibration
│   ├── metrics.py                   # Prometheus metrics
│   └── streamer.py                  # WebSocket telemetry
├── hemolysis_icterus_lipemia_agent/ # Package distribution
│   ├── cli.py                       # Package CLI
│   ├── server.py                    # FastAPI app factory
│   ├── agents.py                    # Coordinator & sub-agents
│   ├── engine.py                    # Clinical domain rules
│   └── models.py                    # Clinical data models
├── tests/                           # Test suite
├── web/                             # Operations console (HTML)
├── docker-compose.yml               # Container orchestration
├── pyproject.toml                   # Package configuration
└── README.md                        # This file
```

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

---

**Author:** Dr. Abu Suraih Sakhri
