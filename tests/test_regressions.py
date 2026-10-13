"""Regression checks for HIL input handling, audit integrity, and browser interface."""
import math
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from agents.base import AuditTrail
from hemolysis_icterus_lipemia_agent.cli import parse_csv_bool
from hil_sentinel import assess_analyte_impact, assess_specimen, classify_hil_index, interpret_hil_indices


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), -1.0])
def test_non_finite_or_negative_hil_rejected(value):
    with pytest.raises(ValueError):
        classify_hil_index("hemolysis", value)
    with pytest.raises(ValueError):
        assess_analyte_impact("potassium", hemolysis=value)


def test_unconfigured_analyte_not_accepted():
    report = assess_specimen(hemolysis=300, analytes=["unknown_test", "potassium"])
    assert report["unassessed_analytes"] == ["unknown_test"]
    assert report["rejected_analytes"] == ["potassium"]
    assert "unknown_test" not in report["accepted_analytes"]


def test_missing_relevant_index_not_accepted():
    assert assess_analyte_impact("potassium", icterus=10)["action"] == "not_assessed"
    assert interpret_hil_indices()["specimen_quality"] == "Not assessed"


@pytest.mark.parametrize("value,expected", [
    ("false", False), ("0", False), ("No", False), ("", False),
    ("true", True), ("1", True), ("YES", True), ("on", True),
])
def test_csv_boolean(value, expected):
    assert parse_csv_bool(value) is expected


def test_invalid_csv_boolean():
    with pytest.raises(ValueError):
        parse_csv_bool("maybe")


def test_audit_hmac_detects_tampering():
    audit = AuditTrail(secret_key="unit-test-secret")
    audit.log("system", "worker", "event", {"status": "OK"})
    audit.log("system", "worker", "event", {"status": "OK"})
    assert audit.verify_integrity()
    snapshot = audit.get_trail()
    snapshot[-1]["actor"] = "changed"
    assert audit.verify_integrity(), "Caller should not be able to mutate audit log"
    audit.logs[-1]["actor"] = "changed"
    assert not audit.verify_integrity(), "Last block must also be authenticated"


def test_web_app_has_executable_javascript():
    html = (Path(__file__).parent.parent / "web" / "index.html").read_text(encoding="utf-8")
    assert "loadPyodide" in html
    assert "HMAC_SHA256_e83f9" not in html
    scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.S)
    assert len(scripts) == 1
    if shutil.which("node"):
        check = subprocess.run(["node", "--check", "-"], input=scripts[0],
                               text=True, capture_output=True, check=False)
        assert check.returncode == 0, check.stderr


def test_unvalidated_corrections_are_opt_in():
    from hil_correction_engine import HILCorrectionEngine
    default = HILCorrectionEngine().correct_analyte("K", 6.8, "H", 20)
    assert not default.correction_applied
    assert default.corrected_value == 6.8
    assert default.confidence == "LOW"
    experimental = HILCorrectionEngine(enable_experimental_corrections=True).correct_analyte("K", 6.8, "H", 20)
    assert experimental.correction_applied
    assert experimental.corrected_value == 6.0


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1.0])
def test_correction_invalid_indices_rejected(value):
    from hil_correction_engine import HILCorrectionEngine
    with pytest.raises(ValueError):
        HILCorrectionEngine().correct_analyte("K", 6.8, "H", value)


def test_mock_does_not_claim_clinical_validation():
    from agents.llm_factory import LLMFactory
    reply = LLMFactory.create("mock").invoke("status")
    assert "No clinical or scientific verification was performed" in reply
    with pytest.raises(ValueError):
        LLMFactory.create("openai")
