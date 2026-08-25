#!/usr/bin/env python3
"""
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
"""

import argparse
import csv
import json
import sys
from typing import Dict, Any, List, Optional, Tuple


# ---------------------------------------------------------------------------
# HIL Index Thresholds
# ---------------------------------------------------------------------------

# Thresholds: (normal_max, mild_max, moderate_max) — above moderate_max = severe
HIL_THRESHOLDS = {
    "hemolysis": {
        "normal_max": 49,
        "mild_max": 100,
        "moderate_max": 250,
        "unit": "H-index",
    },
    "icterus": {
        "normal_max": 19,
        "mild_max": 40,
        "moderate_max": 60,
        "unit": "I-index",
    },
    "lipemia": {
        "normal_max": 99,
        "mild_max": 200,
        "moderate_max": 500,
        "unit": "L-index",
    },
}


# ---------------------------------------------------------------------------
# Analyte Interference Table
# ---------------------------------------------------------------------------

# Each analyte has interference thresholds per HIL type.
# Format: {analyte: {hil_type: (action_at_mild, action_at_moderate, action_at_severe)}}
# Actions: "accept", "flag", "reject"

ANALYTE_INTERFERENCE: Dict[str, Dict[str, Dict[str, Any]]] = {
    "potassium": {
        "hemolysis": {
            "threshold_mild": 50,
            "threshold_moderate": 100,
            "threshold_severe": 250,
            "direction": "falsely_elevated",
            "action_mild": "flag",
            "action_moderate": "reject",
            "action_severe": "reject",
            "note": "Hemolysis releases intracellular K+, causing false elevation. Most common HIL interference.",
        },
    },
    "ldh": {
        "hemolysis": {
            "threshold_mild": 50,
            "threshold_moderate": 100,
            "threshold_severe": 250,
            "direction": "falsely_elevated",
            "action_mild": "flag",
            "action_moderate": "reject",
            "action_severe": "reject",
            "note": "LDH is abundant in RBCs; hemolysis causes significant false elevation.",
        },
    },
    "ast": {
        "hemolysis": {
            "threshold_mild": 100,
            "threshold_moderate": 200,
            "threshold_severe": 300,
            "direction": "falsely_elevated",
            "action_mild": "accept",
            "action_moderate": "flag",
            "action_severe": "reject",
            "note": "AST moderately affected by hemolysis (RBC AST content).",
        },
    },
    "alt": {
        "hemolysis": {
            "threshold_mild": 200,
            "threshold_moderate": 300,
            "threshold_severe": 500,
            "direction": "falsely_elevated",
            "action_mild": "accept",
            "action_moderate": "accept",
            "action_severe": "flag",
            "note": "ALT less affected by hemolysis than AST.",
        },
    },
    "bilirubin": {
        "hemolysis": {
            "threshold_mild": 100,
            "threshold_moderate": 200,
            "threshold_severe": 300,
            "direction": "falsely_decreased",
            "action_mild": "accept",
            "action_moderate": "flag",
            "action_severe": "reject",
            "note": "Hemolysis can cause falsely LOW bilirubin (photometric interference).",
        },
    },
    "haptoglobin": {
        "hemolysis": {
            "threshold_mild": 50,
            "threshold_moderate": 100,
            "threshold_severe": 200,
            "direction": "falsely_decreased",
            "action_mild": "flag",
            "action_moderate": "reject",
            "action_severe": "reject",
            "note": "Hemolysis consumes haptoglobin (binds free hemoglobin), causing true decrease. Interpret with caution.",
        },
    },
    "troponin": {
        "hemolysis": {
            "threshold_mild": 100,
            "threshold_moderate": 200,
            "threshold_severe": 300,
            "direction": "falsely_elevated",
            "action_mild": "accept",
            "action_moderate": "flag",
            "action_severe": "reject",
            "note": "Hemolysis can cause false troponin elevation, especially high-sensitivity assays.",
        },
    },
    "creatinine": {
        "icterus": {
            "threshold_mild": 20,
            "threshold_moderate": 40,
            "threshold_severe": 60,
            "direction": "falsely_elevated",
            "action_mild": "accept",
            "action_moderate": "flag",
            "action_severe": "reject",
            "note": "Jaffe creatinine method is affected by bilirubin. Enzymatic method is preferred in icteric specimens.",
        },
    },
    "triglycerides": {
        "icterus": {
            "threshold_mild": 20,
            "threshold_moderate": 40,
            "threshold_severe": 60,
            "direction": "falsely_elevated",
            "action_mild": "accept",
            "action_moderate": "flag",
            "action_severe": "reject",
            "note": "Bilirubin can interfere with triglyceride assays.",
        },
        "lipemia": {
            "threshold_mild": 200,
            "threshold_moderate": 500,
            "threshold_severe": 800,
            "direction": "falsely_elevated",
            "action_mild": "flag",
            "action_moderate": "reject",
            "action_severe": "reject",
            "note": "Lipemia directly elevates triglycerides (triglycerides ARE the lipemia). Fasting specimen needed.",
        },
    },
    "uric_acid": {
        "icterus": {
            "threshold_mild": 20,
            "threshold_moderate": 40,
            "threshold_severe": 60,
            "direction": "falsely_elevated",
            "action_mild": "accept",
            "action_moderate": "flag",
            "action_severe": "reject",
            "note": "Bilirubin interferes with uric acid measurement (oxidase method).",
        },
    },
    "sodium": {
        "lipemia": {
            "threshold_mild": 200,
            "threshold_moderate": 400,
            "threshold_severe": 600,
            "direction": "falsely_decreased",
            "action_mild": "accept",
            "action_moderate": "flag",
            "action_severe": "reject",
            "note": "Lipemia causes pseudohyponatremia (displacement effect) with indirect ISE methods. Direct ISE is unaffected.",
        },
    },
    "total_protein": {
        "lipemia": {
            "threshold_mild": 200,
            "threshold_moderate": 400,
            "threshold_severe": 600,
            "direction": "falsely_elevated",
            "action_mild": "accept",
            "action_moderate": "flag",
            "action_severe": "reject",
            "note": "Lipemia causes false elevation of turbidimetric protein assays.",
        },
    },
    "amylase": {
        "lipemia": {
            "threshold_mild": 200,
            "threshold_moderate": 400,
            "threshold_severe": 600,
            "direction": "falsely_elevated",
            "action_mild": "accept",
            "action_moderate": "flag",
            "action_severe": "reject",
            "note": "Lipemia can interfere with amylase measurement.",
        },
    },
}


# ---------------------------------------------------------------------------
# HIL Classification
# ---------------------------------------------------------------------------

def classify_hil_index(index_type: str, value: float) -> str:
    """
    Classify an HIL index value as Normal, Mild, Moderate, or Severe.

    Args:
        index_type: 'hemolysis', 'icterus', or 'lipemia'
        value: Index value

    Returns:
        Severity classification string
    """
    key = index_type.strip().lower()
    if key not in HIL_THRESHOLDS:
        raise ValueError(f"Unknown index type '{index_type}'. Use: hemolysis, icterus, lipemia")

    thresholds = HIL_THRESHOLDS[key]
    if value < 0:
        raise ValueError(f"Index value must be non-negative, got {value}")

    if value <= thresholds["normal_max"]:
        return "Normal"
    elif value <= thresholds["mild_max"]:
        return "Mild"
    elif value <= thresholds["moderate_max"]:
        return "Moderate"
    else:
        return "Severe"


def interpret_hil_indices(
    hemolysis: Optional[float] = None,
    icterus: Optional[float] = None,
    lipemia: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Interpret all three HIL indices.

    Returns classification for each index and overall specimen quality.
    """
    result = {
        "hemolysis": None,
        "icterus": None,
        "lipemia": None,
        "specimen_quality": "Acceptable",
        "quality_issues": [],
    }

    if hemolysis is not None:
        h_class = classify_hil_index("hemolysis", hemolysis)
        result["hemolysis"] = {
            "value": hemolysis,
            "classification": h_class,
            "thresholds": HIL_THRESHOLDS["hemolysis"],
        }
        if h_class in ("Moderate", "Severe"):
            result["quality_issues"].append(f"Hemolysis: {h_class} (H-index {hemolysis})")

    if icterus is not None:
        i_class = classify_hil_index("icterus", icterus)
        result["icterus"] = {
            "value": icterus,
            "classification": i_class,
            "thresholds": HIL_THRESHOLDS["icterus"],
        }
        if i_class in ("Moderate", "Severe"):
            result["quality_issues"].append(f"Icterus: {i_class} (I-index {icterus})")

    if lipemia is not None:
        l_class = classify_hil_index("lipemia", lipemia)
        result["lipemia"] = {
            "value": lipemia,
            "classification": l_class,
            "thresholds": HIL_THRESHOLDS["lipemia"],
        }
        if l_class in ("Moderate", "Severe"):
            result["quality_issues"].append(f"Lipemia: {l_class} (L-index {lipemia})")

    if result["quality_issues"]:
        result["specimen_quality"] = "Compromised"

    return result


# ---------------------------------------------------------------------------
# Analyte Impact Assessment
# ---------------------------------------------------------------------------

def assess_analyte_impact(
    analyte: str,
    hemolysis: Optional[float] = None,
    icterus: Optional[float] = None,
    lipemia: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Assess the impact of HIL indices on a specific analyte.

    Returns action (accept/flag/reject) and details for each HIL type.
    """
    analyte_key = analyte.strip().lower().replace(" ", "_")

    if analyte_key not in ANALYTE_INTERFERENCE:
        return {
            "analyte": analyte,
            "action": "accept",
            "details": f"No known HIL interference for {analyte}.",
            "interferences": [],
        }

    interferences = ANALYTE_INTERFERENCE[analyte_key]
    impacts = []
    worst_action = "accept"
    action_priority = {"accept": 0, "flag": 1, "reject": 2}

    for hil_type, hil_value in [("hemolysis", hemolysis), ("icterus", icterus), ("lipemia", lipemia)]:
        if hil_value is None or hil_type not in interferences:
            continue

        config = interferences[hil_type]
        impact = {
            "hil_type": hil_type,
            "hil_value": hil_value,
            "direction": config["direction"],
            "note": config["note"],
        }

        if hil_value <= config["threshold_mild"]:
            impact["action"] = "accept"
            impact["reason"] = f"{hil_type.title()} index {hil_value} below interference threshold."
        elif hil_value <= config["threshold_moderate"]:
            impact["action"] = config["action_mild"]
            impact["reason"] = f"{hil_type.title()} index {hil_value} at mild interference level."
        elif hil_value <= config["threshold_severe"]:
            impact["action"] = config["action_moderate"]
            impact["reason"] = f"{hil_type.title()} index {hil_value} at moderate interference level."
        else:
            impact["action"] = config["action_severe"]
            impact["reason"] = f"{hil_type.title()} index {hil_value} at severe interference level."

        if action_priority.get(impact["action"], 0) > action_priority.get(worst_action, 0):
            worst_action = impact["action"]

        impacts.append(impact)

    return {
        "analyte": analyte,
        "action": worst_action,
        "interferences": impacts,
        "details": (
            f"Overall action for {analyte}: {worst_action.upper()}. "
            + "; ".join(f"{i['hil_type']}: {i['reason']}" for i in impacts)
            if impacts else
            f"No HIL values provided for {analyte} interference assessment."
        ),
    }


# ---------------------------------------------------------------------------
# Full Specimen Assessment
# ---------------------------------------------------------------------------

def assess_specimen(
    hemolysis: Optional[float] = None,
    icterus: Optional[float] = None,
    lipemia: Optional[float] = None,
    analytes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Perform complete HIL specimen assessment.

    Args:
        hemolysis: H-index value
        icterus: I-index value
        lipemia: L-index value
        analytes: List of analytes to assess (default: all known affected analytes)

    Returns:
        Complete assessment with HIL classification and per-analyte impact
    """
    hil_result = interpret_hil_indices(hemolysis, icterus, lipemia)

    if analytes is None:
        analytes = sorted(ANALYTE_INTERFERENCE.keys())

    analyte_impacts = []
    rejected_analytes = []
    flagged_analytes = []
    accepted_analytes = []

    for a in analytes:
        impact = assess_analyte_impact(a, hemolysis, icterus, lipemia)
        analyte_impacts.append(impact)
        if impact["action"] == "reject":
            rejected_analytes.append(a)
        elif impact["action"] == "flag":
            flagged_analytes.append(a)
        else:
            accepted_analytes.append(a)

    return {
        "hil_indices": hil_result,
        "analyte_count": len(analytes),
        "accepted_analytes": accepted_analytes,
        "flagged_analytes": flagged_analytes,
        "rejected_analytes": rejected_analytes,
        "analyte_impacts": analyte_impacts,
        "overall_recommendation": (
            f"REJECT specimen for: {', '.join(rejected_analytes)}. "
            f"FLAG with caution: {', '.join(flagged_analytes)}. "
            f"ACCEPT: {', '.join(accepted_analytes)}."
            if (rejected_analytes or flagged_analytes) else
            "All analytes acceptable. No HIL interference detected."
        ),
    }


# ---------------------------------------------------------------------------
# Batch Processing
# ---------------------------------------------------------------------------

def process_batch(input_csv: str, output_csv: str) -> int:
    """
    Process a CSV of HIL index values and assess each specimen.

    Expected columns: hemolysis, icterus, lipemia
    Optional: analytes (comma-separated list)
    """
    with open(input_csv, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    out_fields = fieldnames + [
        "h_classification", "i_classification", "l_classification",
        "specimen_quality", "rejected_analytes", "flagged_analytes", "recommendation",
    ]
    out_rows = []

    for r in rows:
        try:
            h = float(r["hemolysis"]) if r.get("hemolysis") else None
            i = float(r["icterus"]) if r.get("icterus") else None
            l = float(r["lipemia"]) if r.get("lipemia") else None

            analytes_str = r.get("analytes", "")
            analytes = [a.strip() for a in analytes_str.split(",") if a.strip()] if analytes_str else None

            result = assess_specimen(h, i, l, analytes)

            row_dict = dict(r)
            hil = result["hil_indices"]
            row_dict["h_classification"] = hil["hemolysis"]["classification"] if hil["hemolysis"] else ""
            row_dict["i_classification"] = hil["icterus"]["classification"] if hil["icterus"] else ""
            row_dict["l_classification"] = hil["lipemia"]["classification"] if hil["lipemia"] else ""
            row_dict["specimen_quality"] = hil["specimen_quality"]
            row_dict["rejected_analytes"] = ", ".join(result["rejected_analytes"])
            row_dict["flagged_analytes"] = ", ".join(result["flagged_analytes"])
            row_dict["recommendation"] = result["overall_recommendation"]
        except (ValueError, KeyError) as e:
            row_dict = dict(r)
            row_dict["h_classification"] = f"ERROR: {e}"
            row_dict["i_classification"] = ""
            row_dict["l_classification"] = ""
            row_dict["specimen_quality"] = ""
            row_dict["rejected_analytes"] = ""
            row_dict["flagged_analytes"] = ""
            row_dict["recommendation"] = ""

        out_rows.append(row_dict)

    with open(output_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(out_rows)

    return len(out_rows)
