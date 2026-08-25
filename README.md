# HIL — Hemolysis, Icterus, Lipemia Index Interpreter

A zero-dependency Python tool for interpreting spectrophotometric HIL interference indices and determining their impact on clinical analyte results.

## HIL Index Classification

### Hemolysis (H-index)

| Level | Range | Clinical Action |
|-------|-------|----------------|
| Normal | 0 – 49 | No interference expected |
| Mild | 50 – 100 | May affect sensitive analytes |
| Moderate | 100 – 250 | Significant interference likely |
| Severe | > 250 | Reject for most affected analytes |

### Icterus (I-index)

| Level | Range | Clinical Action |
|-------|-------|----------------|
| Normal | 0 – 19 | No interference expected |
| Mild | 20 – 40 | Monitor affected analytes |
| Moderate | 40 – 60 | Flag or reject affected analytes |
| Severe | > 60 | Reject for most affected analytes |

### Lipemia (L-index)

| Level | Range | Clinical Action |
|-------|-------|----------------|
| Normal | 0 – 99 | No interference expected |
| Mild | 100 – 200 | May affect turbidimetric assays |
| Moderate | 200 – 500 | Significant interference |
| Severe | > 500 | Reject for most affected analytes |

## Affected Analytes

### Hemolysis Affects
| Analyte | Direction | Mild | Moderate | Severe |
|---------|-----------|------|----------|--------|
| Potassium | ↑ Falsely elevated | Flag | Reject | Reject |
| LDH | ↑ Falsely elevated | Flag | Reject | Reject |
| AST | ↑ Falsely elevated | Accept | Flag | Reject |
| ALT | ↑ Falsely elevated | Accept | Accept | Flag |
| Bilirubin | ↓ Falsely decreased | Accept | Flag | Reject |
| Haptoglobin | ↓ Falsely decreased | Flag | Reject | Reject |
| Troponin | ↑ Falsely elevated | Accept | Flag | Reject |

### Icterus Affects
| Analyte | Direction | Mild | Moderate | Severe |
|---------|-----------|------|----------|--------|
| Creatinine (Jaffe) | ↑ Falsely elevated | Accept | Flag | Reject |
| Triglycerides | ↑ Falsely elevated | Accept | Flag | Reject |
| Uric acid | ↑ Falsely elevated | Accept | Flag | Reject |

### Lipemia Affects
| Analyte | Direction | Mild | Moderate | Severe |
|---------|-----------|------|----------|--------|
| Sodium | ↓ Falsely decreased | Accept | Flag | Reject |
| Triglycerides | ↑ Falsely elevated | Flag | Reject | Reject |
| Total protein | ↑ Falsely elevated | Accept | Flag | Reject |
| Amylase | ↑ Falsely elevated | Accept | Flag | Reject |

## Quick Start

```bash
# Interpret HIL indices
python cli.py interpret --hemolysis 150 --icterus 25 --lipemia 300

# Assess impact on specific analyte
python cli.py analyte --analyte potassium --hemolysis 150

# Full specimen assessment
python cli.py specimen --hemolysis 150 --icterus 25 --lipemia 300

# List all analytes with interference data
python cli.py list-analytes

# Batch processing
python cli.py batch -i specimens.csv -o results.csv
```

### Python API

```python
from hil_sentinel import assess_specimen, assess_analyte_impact

# Full specimen assessment
result = assess_specimen(hemolysis=300, icterus=25, lipemia=100)
print(result["rejected_analytes"])   # ['potassium', 'ldh', 'haptoglobin']
print(result["flagged_analytes"])    # ['ast', 'bilirubin', 'troponin', ...]

# Single analyte
impact = assess_analyte_impact("potassium", hemolysis=150)
print(impact["action"])  # "flag"
```

## Running Tests

```bash
python -m pytest test_hil_sentinel.py -v
```

## License

MIT License.
