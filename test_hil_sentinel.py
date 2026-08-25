#!/usr/bin/env python3
"""Tests for HIL (Hemolysis, Icterus, Lipemia) Index Interpreter."""
import json
import os
import tempfile
import unittest

from hil_sentinel import (
    classify_hil_index,
    interpret_hil_indices,
    assess_analyte_impact,
    assess_specimen,
    process_batch,
    HIL_THRESHOLDS,
    ANALYTE_INTERFERENCE,
)


class TestClassifyHILIndex(unittest.TestCase):
    """Test HIL index classification."""

    # Hemolysis
    def test_hemolysis_normal(self):
        self.assertEqual(classify_hil_index("hemolysis", 0), "Normal")
        self.assertEqual(classify_hil_index("hemolysis", 49), "Normal")

    def test_hemolysis_mild(self):
        self.assertEqual(classify_hil_index("hemolysis", 50), "Mild")
        self.assertEqual(classify_hil_index("hemolysis", 100), "Mild")

    def test_hemolysis_moderate(self):
        self.assertEqual(classify_hil_index("hemolysis", 101), "Moderate")
        self.assertEqual(classify_hil_index("hemolysis", 250), "Moderate")

    def test_hemolysis_severe(self):
        self.assertEqual(classify_hil_index("hemolysis", 251), "Severe")
        self.assertEqual(classify_hil_index("hemolysis", 500), "Severe")

    # Icterus
    def test_icterus_normal(self):
        self.assertEqual(classify_hil_index("icterus", 0), "Normal")
        self.assertEqual(classify_hil_index("icterus", 19), "Normal")

    def test_icterus_mild(self):
        self.assertEqual(classify_hil_index("icterus", 20), "Mild")
        self.assertEqual(classify_hil_index("icterus", 40), "Mild")

    def test_icterus_moderate(self):
        self.assertEqual(classify_hil_index("icterus", 41), "Moderate")
        self.assertEqual(classify_hil_index("icterus", 60), "Moderate")

    def test_icterus_severe(self):
        self.assertEqual(classify_hil_index("icterus", 61), "Severe")

    # Lipemia
    def test_lipemia_normal(self):
        self.assertEqual(classify_hil_index("lipemia", 0), "Normal")
        self.assertEqual(classify_hil_index("lipemia", 99), "Normal")

    def test_lipemia_mild(self):
        self.assertEqual(classify_hil_index("lipemia", 100), "Mild")
        self.assertEqual(classify_hil_index("lipemia", 200), "Mild")

    def test_lipemia_moderate(self):
        self.assertEqual(classify_hil_index("lipemia", 201), "Moderate")
        self.assertEqual(classify_hil_index("lipemia", 500), "Moderate")

    def test_lipemia_severe(self):
        self.assertEqual(classify_hil_index("lipemia", 501), "Severe")

    def test_invalid_type_raises(self):
        with self.assertRaises(ValueError):
            classify_hil_index("unknown", 50)

    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            classify_hil_index("hemolysis", -1)


class TestInterpretHILIndices(unittest.TestCase):
    """Test HIL index interpretation."""

    def test_all_normal(self):
        result = interpret_hil_indices(10, 5, 50)
        self.assertEqual(result["specimen_quality"], "Acceptable")
        self.assertEqual(len(result["quality_issues"]), 0)

    def test_mild_hemolysis(self):
        result = interpret_hil_indices(hemolysis=75)
        self.assertEqual(result["hemolysis"]["classification"], "Mild")
        self.assertEqual(result["specimen_quality"], "Acceptable")

    def test_severe_hemolysis(self):
        result = interpret_hil_indices(hemolysis=300)
        self.assertEqual(result["hemolysis"]["classification"], "Severe")
        self.assertEqual(result["specimen_quality"], "Compromised")
        self.assertTrue(len(result["quality_issues"]) > 0)

    def test_moderate_icterus(self):
        result = interpret_hil_indices(icterus=50)
        self.assertEqual(result["icterus"]["classification"], "Moderate")
        self.assertEqual(result["specimen_quality"], "Compromised")

    def test_severe_lipemia(self):
        result = interpret_hil_indices(lipemia=600)
        self.assertEqual(result["lipemia"]["classification"], "Severe")
        self.assertEqual(result["specimen_quality"], "Compromised")

    def test_multiple_issues(self):
        result = interpret_hil_indices(hemolysis=200, icterus=50, lipemia=600)
        self.assertEqual(result["specimen_quality"], "Compromised")
        self.assertEqual(len(result["quality_issues"]), 3)


class TestAssessAnalyteImpact(unittest.TestCase):
    """Test per-analyte interference assessment."""

    def test_potassium_mild_hemolysis_flag(self):
        """K+ with mild hemolysis should be flagged."""
        result = assess_analyte_impact("potassium", hemolysis=75)
        self.assertEqual(result["action"], "flag")

    def test_potassium_severe_hemolysis_reject(self):
        """K+ with severe hemolysis should be rejected."""
        result = assess_analyte_impact("potassium", hemolysis=300)
        self.assertEqual(result["action"], "reject")

    def test_potassium_no_hemolysis_accept(self):
        """K+ with no hemolysis should be accepted."""
        result = assess_analyte_impact("potassium", hemolysis=10)
        self.assertEqual(result["action"], "accept")

    def test_ldh_moderate_hemolysis_reject(self):
        """LDH with moderate hemolysis should be rejected."""
        result = assess_analyte_impact("ldh", hemolysis=150)
        self.assertEqual(result["action"], "reject")

    def test_creatinine_moderate_icterus_flag(self):
        """Creatinine with moderate icterus should be flagged (Jaffe method)."""
        result = assess_analyte_impact("creatinine", icterus=50)
        self.assertEqual(result["action"], "flag")

    def test_creatinine_severe_icterus_reject(self):
        result = assess_analyte_impact("creatinine", icterus=70)
        self.assertEqual(result["action"], "reject")

    def test_sodium_moderate_lipemia_flag(self):
        """Sodium with moderate lipemia should be flagged (pseudohyponatremia)."""
        result = assess_analyte_impact("sodium", lipemia=450)
        self.assertEqual(result["action"], "flag")

    def test_triglycerides_lipemia_reject(self):
        """Triglycerides with moderate lipemia should be rejected."""
        result = assess_analyte_impact("triglycerides", lipemia=600)
        self.assertEqual(result["action"], "reject")

    def test_unknown_analyte_accept(self):
        """Unknown analyte should be accepted (no known interference)."""
        result = assess_analyte_impact("troponin_t", hemolysis=300)
        self.assertEqual(result["action"], "accept")

    def test_ast_mild_hemolysis_accept(self):
        """AST with mild hemolysis should be accepted."""
        result = assess_analyte_impact("ast", hemolysis=75)
        self.assertEqual(result["action"], "accept")

    def test_ast_severe_hemolysis_reject(self):
        """AST with severe hemolysis should be rejected."""
        result = assess_analyte_impact("ast", hemolysis=350)
        self.assertEqual(result["action"], "reject")

    def test_total_protein_moderate_lipemia_flag(self):
        result = assess_analyte_impact("total_protein", lipemia=450)
        self.assertEqual(result["action"], "flag")

    def test_direction_in_result(self):
        """Result should include direction of interference."""
        result = assess_analyte_impact("potassium", hemolysis=75)
        self.assertEqual(result["interferences"][0]["direction"], "falsely_elevated")


class TestAssessSpecimen(unittest.TestCase):
    """Test full specimen assessment."""

    def test_clean_specimen(self):
        result = assess_specimen(hemolysis=10, icterus=5, lipemia=50)
        self.assertEqual(len(result["rejected_analytes"]), 0)
        self.assertEqual(len(result["flagged_analytes"]), 0)

    def test_hemolyzed_specimen(self):
        result = assess_specimen(hemolysis=300)
        self.assertIn("potassium", result["rejected_analytes"])
        self.assertIn("ldh", result["rejected_analytes"])

    def test_icteric_specimen(self):
        result = assess_specimen(icterus=70)
        self.assertIn("creatinine", result["rejected_analytes"])

    def test_lipemic_specimen(self):
        result = assess_specimen(lipemia=600)
        self.assertIn("triglycerides", result["rejected_analytes"])

    def test_custom_analytes(self):
        result = assess_specimen(hemolysis=300, analytes=["potassium", "glucose"])
        self.assertIn("potassium", result["rejected_analytes"])
        # glucose is not affected by hemolysis
        self.assertNotIn("glucose", result["rejected_analytes"])

    def test_recommendation_present(self):
        result = assess_specimen(hemolysis=300)
        self.assertIn("REJECT", result["overall_recommendation"])


class TestProcessBatch(unittest.TestCase):
    """Test batch processing."""

    def test_batch_basic(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = os.path.join(tmp, "in.csv")
            out = os.path.join(tmp, "out.csv")
            with open(inp, "w") as f:
                f.write("hemolysis,icterus,lipemia\n")
                f.write("10,5,50\n")
                f.write("300,5,50\n")
                f.write("10,70,50\n")
            n = process_batch(inp, out)
            self.assertEqual(n, 3)
            with open(out) as f:
                content = f.read()
                self.assertIn("specimen_quality", content)
                self.assertIn("Compromised", content)
                self.assertIn("Acceptable", content)

    def test_batch_with_analytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = os.path.join(tmp, "in.csv")
            out = os.path.join(tmp, "out.csv")
            with open(inp, "w") as f:
                f.write('hemolysis,icterus,lipemia,analytes\n')
                f.write('300,5,50,"potassium,ldh"\n')
            n = process_batch(inp, out)
            self.assertEqual(n, 1)


class TestCLI(unittest.TestCase):
    """Test CLI interface."""

    def test_cli_interpret(self):
        from cli import main
        ret = main(["interpret", "--hemolysis", "150", "--icterus", "25", "--lipemia", "300"])
        self.assertEqual(ret, 0)

    def test_cli_analyte(self):
        from cli import main
        ret = main(["analyte", "--analyte", "potassium", "--hemolysis", "150"])
        self.assertEqual(ret, 0)

    def test_cli_specimen(self):
        from cli import main
        ret = main(["specimen", "--hemolysis", "300", "--icterus", "5", "--lipemia", "50"])
        self.assertEqual(ret, 0)

    def test_cli_list_analytes(self):
        from cli import main
        ret = main(["list-analytes"])
        self.assertEqual(ret, 0)

    def test_cli_batch(self):
        from cli import main
        with tempfile.TemporaryDirectory() as tmp:
            inp = os.path.join(tmp, "in.csv")
            out = os.path.join(tmp, "out.csv")
            with open(inp, "w") as f:
                f.write("hemolysis,icterus,lipemia\n10,5,50\n")
            ret = main(["batch", "-i", inp, "-o", out])
            self.assertEqual(ret, 0)


if __name__ == "__main__":
    unittest.main()
