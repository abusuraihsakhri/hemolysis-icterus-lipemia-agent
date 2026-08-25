#!/usr/bin/env python3
"""
HIL Correction Engine: Analyte-Specific HIL Interference Correction Factors
Applies published correction formulas to provide corrected analyte values when
Hemolysis (H), Icterus (I), or Lipemia (L) indices indicate interference.

Domain: Laboratory Medicine — Pre-Analytical Quality
Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import datetime
import json
import math
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple


@dataclass
class CorrectionResult:
    """Result of an analyte correction computation."""
    result_id: str
    analyte_code: str
    raw_value: float
    corrected_value: float
    hil_index_type: str  # H, I, or L
    hil_index_value: float
    correction_factor: float
    correction_formula: str
    confidence: str  # HIGH, MODERATE, LOW
    correction_applied: bool
    notes: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Published correction factor table: (analyte_code, hil_type) -> (formula_type, factor, description)
CORRECTION_FACTOR_TABLE: Dict[Tuple[str, str], Dict[str, Any]] = {
    # Hemolysis corrections
    ("K", "H"): {
        "formula_type": "linear_subtraction",
        "factor": 0.04,
        "description": "K+ correction: corrected = measured - (H-index × 0.04). Hemolysis falsely elevates K+.",
        "reference": "CLSI C56-A; Lippi et al. 2006",
        "confidence": "HIGH",
        "applicable_range": (0, 500),
    },
    ("LDH", "H"): {
        "formula_type": "linear_subtraction",
        "factor": 0.08,
        "description": "LDH correction: corrected = measured - (H-index × 0.08). RBC LDH release.",
        "reference": "CLSI C56-A",
        "confidence": "HIGH",
        "applicable_range": (0, 500),
    },
    ("AST", "H"): {
        "formula_type": "linear_subtraction",
        "factor": 0.06,
        "description": "AST correction: corrected = measured - (H-index × 0.06). RBC AST release.",
        "reference": "CLSI C56-A; Nikolac et al. 2017",
        "confidence": "HIGH",
        "applicable_range": (0, 500),
    },
    ("ALT", "H"): {
        "formula_type": "linear_subtraction",
        "factor": 0.02,
        "description": "ALT correction: corrected = measured - (H-index × 0.02). Minor RBC ALT contribution.",
        "reference": "CLSI C56-A",
        "confidence": "MODERATE",
        "applicable_range": (0, 500),
    },
    ("TROPT", "H"): {
        "formula_type": "flag_only",
        "factor": 0.0,
        "description": "Troponin T/I: No reliable correction formula. Flag as potentially unreliable.",
        "reference": "IFCC Task Force on Cardiac Biomarkers",
        "confidence": "LOW",
        "applicable_range": (0, 100),
    },
    ("BILIRUBIN", "H"): {
        "formula_type": "linear_subtraction",
        "factor": 0.01,
        "description": "Total bilirubin minor correction for hemolysis interference.",
        "reference": "CLSI C56-A",
        "confidence": "MODERATE",
        "applicable_range": (0, 300),
    },
    # Icterus corrections
    ("CR_JAFFE", "I"): {
        "formula_type": "linear_subtraction",
        "factor": 0.015,
        "description": "Creatinine Jaffe method correction for icterus. corrected = measured - (I-index × 0.015).",
        "reference": "CLSI C56-A; Weber et al. 2013",
        "confidence": "HIGH",
        "applicable_range": (0, 40),
    },
    ("TBILIRUBIN", "I"): {
        "formula_type": "flag_only",
        "factor": 0.0,
        "description": "Total bilirubin: No correction needed (icterus is the analyte itself). Flag for extreme values.",
        "reference": "CLSI C56-A",
        "confidence": "HIGH",
        "applicable_range": (0, 40),
    },
    ("CHOL", "I"): {
        "formula_type": "linear_subtraction",
        "factor": 0.01,
        "description": "Cholesterol minor correction for bilirubin interference in certain assay methods.",
        "reference": "Dimeski et al. 2010",
        "confidence": "MODERATE",
        "applicable_range": (0, 40),
    },
    # Lipemia corrections
    ("TG", "L"): {
        "formula_type": "flag_only",
        "factor": 0.0,
        "description": "Triglycerides: Lipemia is the source. No correction; flag for ultracentrifugation.",
        "reference": "CLSI C56-A",
        "confidence": "HIGH",
        "applicable_range": (0, 1000),
    },
    ("HGB", "L"): {
        "formula_type": "linear_subtraction",
        "factor": 0.003,
        "description": "Hemoglobin spectrophotometric correction for lipemia. corrected = measured - (L-index × 0.003).",
        "reference": "CLSI H15-A3",
        "confidence": "MODERATE",
        "applicable_range": (0, 1000),
    },
    ("NA", "L"): {
        "formula_type": "flag_only",
        "factor": 0.0,
        "description": "Sodium: Lipemia may cause pseudohyponatremia with indirect ISE. Flag for direct ISE confirmation.",
        "reference": "Dimeski et al. 2010",
        "confidence": "MODERATE",
        "applicable_range": (0, 1000),
    },
}


class HILCorrectionEngine:
    """
    Applies published correction formulas to analyte values when HIL indices
    indicate pre-analytical interference.
    """

    def __init__(self, custom_table: Optional[Dict] = None):
        self.correction_table = custom_table or CORRECTION_FACTOR_TABLE

    def correct_analyte(
        self,
        analyte_code: str,
        raw_value: float,
        hil_index_type: str,
        hil_index_value: float,
    ) -> CorrectionResult:
        """
        Apply correction formula for a given analyte given HIL interference.

        Args:
            analyte_code: Laboratory analyte code (e.g., 'K', 'AST', 'CR_JAFFE')
            raw_value: Measured analyte value
            hil_index_type: HIL index type ('H', 'I', or 'L')
            hil_index_value: HIL index value (0-1000 scale)

        Returns:
            CorrectionResult with corrected value and confidence assessment
        """
        key = (analyte_code.upper(), hil_index_type.upper())
        entry = self.correction_table.get(key)

        if entry is None:
            return CorrectionResult(
                result_id=str(uuid.uuid4())[:8],
                analyte_code=analyte_code,
                raw_value=raw_value,
                corrected_value=raw_value,
                hil_index_type=hil_index_type,
                hil_index_value=hil_index_value,
                correction_factor=0.0,
                correction_formula="NO_CORRECTION_AVAILABLE",
                confidence="LOW",
                correction_applied=False,
                notes=[f"No correction formula available for {analyte_code} with {hil_index_type}-index interference."],
            )

        formula_type = entry["formula_type"]
        factor = entry["factor"]
        lo, hi = entry["applicable_range"]

        notes = []
        correction_applied = False
        corrected_value = raw_value

        if hil_index_value < lo or hil_index_value > hi:
            notes.append(f"HIL index {hil_index_value} outside applicable range ({lo}-{hi}). Correction not applied.")
        elif formula_type == "flag_only":
            notes.append(entry["description"])
            notes.append("No numerical correction possible. Flag for manual review.")
        elif formula_type == "linear_subtraction":
            correction_amount = hil_index_value * factor
            corrected_value = raw_value - correction_amount
            if corrected_value < 0:
                corrected_value = 0.0
                notes.append("Corrected value clamped to 0 (negative result after correction).")
            correction_applied = True
            notes.append(entry["description"])
        else:
            notes.append(f"Unknown formula type: {formula_type}")

        return CorrectionResult(
            result_id=str(uuid.uuid4())[:8],
            analyte_code=analyte_code,
            raw_value=raw_value,
            corrected_value=round(corrected_value, 4),
            hil_index_type=hil_index_type,
            hil_index_value=hil_index_value,
            correction_factor=factor,
            correction_formula=formula_type,
            confidence=entry.get("confidence", "MODERATE"),
            correction_applied=correction_applied,
            notes=notes,
        )

    def get_available_corrections(self) -> List[Dict[str, Any]]:
        """Return list of all available correction formulas."""
        results = []
        for (analyte, hil_type), entry in self.correction_table.items():
            results.append({
                "analyte": analyte,
                "hil_type": hil_type,
                "formula_type": entry["formula_type"],
                "factor": entry["factor"],
                "description": entry["description"],
                "reference": entry.get("reference", ""),
                "confidence": entry.get("confidence", "MODERATE"),
            })
        return results

    def batch_correct(
        self,
        analytes: List[Dict[str, Any]],
        hil_indices: Dict[str, float],
    ) -> List[CorrectionResult]:
        """
        Correct multiple analytes against HIL indices.

        Args:
            analytes: List of dicts with 'code' and 'value' keys
            hil_indices: Dict mapping HIL type to value, e.g. {'H': 150, 'I': 10, 'L': 50}

        Returns:
            List of CorrectionResult for each analyte × HIL combination where correction exists
        """
        results = []
        for analyte in analytes:
            code = analyte.get("code", "")
            value = float(analyte.get("value", 0))
            for hil_type, hil_val in hil_indices.items():
                if hil_val > 0:
                    result = self.correct_analyte(code, value, hil_type, hil_val)
                    results.append(result)
        return results


def main():
    """CLI entry point for HIL correction engine."""
    import argparse

    parser = argparse.ArgumentParser(description="HIL Correction Engine")
    parser.add_argument("--analyte", type=str, required=True, help="Analyte code (e.g., K, AST, CR_JAFFE)")
    parser.add_argument("--raw", type=float, required=True, help="Raw measured value")
    parser.add_argument("--hil-type", type=str, required=True, choices=["H", "I", "L"], help="HIL index type")
    parser.add_argument("--hil-value", type=float, required=True, help="HIL index value")
    parser.add_argument("--list", action="store_true", help="List all available corrections")
    args = parser.parse_args()

    engine = HILCorrectionEngine()

    if args.list:
        corrections = engine.get_available_corrections()
        print(json.dumps(corrections, indent=2))
        return

    result = engine.correct_analyte(args.analyte, args.raw, args.hil_type, args.hil_value)
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
