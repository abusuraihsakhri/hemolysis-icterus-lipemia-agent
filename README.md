# Hemolysis–Icterus–Lipemia (HIL) Index Interpreter

A Python laboratory-medicine research utility for classifying HIL indices, screening example analyte-specific interference rules, and generating specimen summaries. It also contains experimental correction, trend, specimen-quality, agent, and API modules.

**Not a validated clinical decision system.** HIL index units and interference limits depend on the analyzer, assay method, reagents, and local verification data. The bundled cutoffs and interference rules are examples only; they must not determine patient-result release, suppression, correction, or specimen rejection.

## Browser application

The repository contains a browser-based interface at `web/index.html`. When GitHub Pages publishes the repository root, `index.html` redirects to that interface. It loads the local `hil_sentinel.py` module using [Pyodide](https://pyodide.org/) and executes the Python assessment **in the browser**, without a Python server.

The first visit requires an internet connection to download Pyodide from a public CDN. The values entered in the form are processed locally, not sent to an application backend. The page supports individual H, I, and L inputs, optional analyte filtering, classifications, example actions, and JSON export. Browser-run Python is limited to the HIL index interpreter; FastAPI and the other server-side modules are not run in-browser.

For local use, from the repository root:

```bash
python -m http.server 8080
# Visit http://127.0.0.1:8080/
```

Do not enter patient identifiers. The UI contains no claim of PHI de-identification or HIPAA compliance.

## Command-line usage

Requires Python 3.9 or newer. Python 3.10–3.12 are covered by CI.

```bash
python -m pip install -e ".[dev]"
python -m pytest -v

python cli.py interpret --hemolysis 150 --icterus 25 --lipemia 300
python cli.py analyte --analyte potassium --hemolysis 150
python cli.py specimen --hemolysis 150 --icterus 25 --lipemia 300
python cli.py list-analytes
python cli.py batch -i sample_hil.csv -o results.csv
```

For package-level audit, chat, and CSV-batch workflows:

```bash
python -m hemolysis_icterus_lipemia_agent.cli audit --case-id SYNTH-001
python -m hemolysis_icterus_lipemia_agent.cli verify-audit
python -m hemolysis_icterus_lipemia_agent.cli batch -i sample.csv -o results.csv
```

These are distinct entry points: the root `cli.py` operates the HIL interpreter; the packaged CLI operates the separate generic agent workflow. Generic "primary" and "secondary" metrics are not equivalent to independent H, I, and L measurements.

## APIs and containers

```bash
python -m pip install -e ".[server]"
python -m hemolysis_icterus_lipemia_agent.cli serve --host 127.0.0.1 --port 8000
# GET http://127.0.0.1:8000/health
```

The `agents.api` module also exposes a distinct agent API, accessible with `uvicorn agents.api:app --host 127.0.0.1 --port 8000`. These APIs are **not authenticated** and must not be publicly exposed or used for identifiable patient data without appropriate security engineering and validation.

For Docker Compose, set a strong persistent `AUDIT_SECRET_KEY` before starting the service. Compose binds port 8000 to localhost.

```bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
docker compose up --build
```

## Research modules

- `hil_sentinel.py`: H/I/L classification, example analyte-specific actions, specimen evaluation, batch CSV.
- `hil_correction_engine.py`: experimental coefficients and flag-only rules. **Numerical corrections are not validated across instruments or methods and must not be used clinically.** Numerical correction is disabled by default; `--experimental-corrections` opts in for research calculations. `python hil_correction_engine.py --list` lists examples.
- `hil_trend_tracker.py`: site/shift summaries and box-plot data.
- `specimen_quality_scorer.py`: example composite specimen-quality score.
- `enrichment.py`: demonstration enrichment routines.
- `agents/`: structured orchestration, regex-based identifier screening, and in-memory HMAC-chained audit records.
- `hemolysis_icterus_lipemia_agent/`: packaged agent CLI and optional FastAPI service.

Unknown analytes or missing relevant HIL measurements are reported as `not_assessed`, never silently interpreted as safe. Where an example rule reports accept/flag/reject, the decision is **illustrative**, not clinically authoritative.

## Security and privacy

The browser interface performs calculations locally and does not send entered HIL data to the application server. It downloads the Pyodide runtime from a third-party CDN and links to this public repository. The Python API includes regex-based identifier screening, which is **not sufficient to guarantee de-identification**. Audit logging is memory-resident and HMAC-chained but is not a durable, independently verified compliance system; set `AUDIT_SECRET_KEY` when audit continuity matters. Avoid uploading or sending patient-identifying information.

## Testing and compatibility

CI tests Python 3.10, 3.11, and 3.12 with pytest. Static JavaScript syntax is checked with Node when available. The Pyodide browser application targets modern browsers with WebAssembly support; actual browser runtime depends on the availability of the public CDN.

## License

[MIT](LICENSE).
