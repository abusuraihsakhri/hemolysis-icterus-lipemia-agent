#!/usr/bin/env python3
"""
CLI for HIL (Hemolysis, Icterus, Lipemia) Index Interpreter.

Usage:
  python cli.py interpret --hemolysis 150 --icterus 25 --lipemia 300
  python cli.py analyte --analyte potassium --hemolysis 150
  python cli.py specimen --hemolysis 150 --icterus 25 --lipemia 300
  python cli.py batch -i specimens.csv -o results.csv
"""
import argparse
import json
import sys

from hil_sentinel import (
    classify_hil_index,
    interpret_hil_indices,
    assess_analyte_impact,
    assess_specimen,
    process_batch,
    HIL_THRESHOLDS,
    ANALYTE_INTERFERENCE,
)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="hil-interpreter",
        description="HIL (Hemolysis, Icterus, Lipemia) Index Interpreter",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Interpret HIL indices
    p_interp = subparsers.add_parser("interpret", help="Interpret HIL indices")
    p_interp.add_argument("--hemolysis", type=float, default=None, help="H-index value")
    p_interp.add_argument("--icterus", type=float, default=None, help="I-index value")
    p_interp.add_argument("--lipemia", type=float, default=None, help="L-index value")

    # Single analyte impact
    p_analyte = subparsers.add_parser("analyte", help="Assess impact on a specific analyte")
    p_analyte.add_argument("--analyte", required=True, help="Analyte name")
    p_analyte.add_argument("--hemolysis", type=float, default=None, help="H-index")
    p_analyte.add_argument("--icterus", type=float, default=None, help="I-index")
    p_analyte.add_argument("--lipemia", type=float, default=None, help="L-index")

    # Full specimen assessment
    p_spec = subparsers.add_parser("specimen", help="Full specimen assessment")
    p_spec.add_argument("--hemolysis", type=float, default=None, help="H-index")
    p_spec.add_argument("--icterus", type=float, default=None, help="I-index")
    p_spec.add_argument("--lipemia", type=float, default=None, help="L-index")
    p_spec.add_argument("--analytes", type=str, default=None,
                        help="Comma-separated list of analytes (default: all)")

    # List analytes
    subparsers.add_parser("list-analytes", help="List all analytes with interference data")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV")
    p_batch.add_argument("-i", "--input", required=True, help="Input CSV")
    p_batch.add_argument("-o", "--output", default="results.csv", help="Output CSV")

    args = parser.parse_args(argv)

    if args.command == "interpret":
        result = interpret_hil_indices(args.hemolysis, args.icterus, args.lipemia)
        print(json.dumps(result, indent=2))

    elif args.command == "analyte":
        result = assess_analyte_impact(args.analyte, args.hemolysis, args.icterus, args.lipemia)
        print(json.dumps(result, indent=2))

    elif args.command == "specimen":
        analytes = [a.strip() for a in args.analytes.split(",")] if args.analytes else None
        result = assess_specimen(args.hemolysis, args.icterus, args.lipemia, analytes)
        print(json.dumps(result, indent=2))

    elif args.command == "list-analytes":
        print(f"{'Analyte':<20} {'HIL Type':<12} {'Direction':<20}")
        print("-" * 55)
        for analyte, interferences in sorted(ANALYTE_INTERFERENCE.items()):
            for hil_type, config in interferences.items():
                print(f"{analyte:<20} {hil_type:<12} {config['direction']:<20}")

    elif args.command == "batch":
        n = process_batch(args.input, args.output)
        print(f"Processed {n} records -> {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
