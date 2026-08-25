#!/usr/bin/env python3
"""
HIL Trend Tracker: Index Trending by Collection Site and Phlebotomy Shift
Identifies systemic pre-analytical issues by tracking HIL indices across
collection locations and phlebotomy shifts.

Domain: Laboratory Medicine — Pre-Analytical Quality
Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import datetime
import json
import math
import uuid
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple


@dataclass
class HILReading:
    """A single HIL index reading with collection metadata."""
    reading_id: str
    collection_site: str
    shift: str  # DAY, EVENING, NIGHT
    hil_h: float
    hil_i: float
    hil_l: float
    collection_date: str
    accession_id: str = ""
    phlebotomist_id: str = ""
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SiteShiftStatistics:
    """Statistical summary for a site/shift combination."""
    collection_site: str
    shift: str
    hil_type: str
    count: int
    mean: float
    median: float
    p95: float
    min_val: float
    max_val: float
    std_dev: float
    flag_rate: float  # percentage of readings above flagging threshold

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrendReport:
    """Aggregated trend report for HIL indices."""
    report_id: str
    period_start: str
    period_end: str
    total_readings: int
    site_shift_stats: List[SiteShiftStatistics]
    outlier_sites: List[Dict[str, Any]]
    generated_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Default HIL flagging thresholds (CLSI-based)
DEFAULT_HIL_THRESHOLDS = {
    "H": 100,   # Hemolysis index flag threshold
    "I": 20,    # Icterus index flag threshold
    "L": 150,   # Lipemia index flag threshold
}


class HILTrendTracker:
    """
    Tracks and analyzes HIL index trends by collection site and phlebotomy shift
    to identify systemic pre-analytical issues.
    """

    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        self.readings: List[HILReading] = []
        self.thresholds = thresholds or DEFAULT_HIL_THRESHOLDS

    def add_reading(self, reading: HILReading) -> None:
        """Add a single HIL reading to the tracker."""
        self.readings.append(reading)

    def ingest_batch(self, records: List[Dict[str, Any]]) -> int:
        """
        Ingest a batch of HIL reading records.

        Args:
            records: List of dicts with keys: collection_site, shift, hil_h, hil_i, hil_l, collection_date

        Returns:
            Number of records ingested
        """
        count = 0
        for rec in records:
            reading = HILReading(
                reading_id=str(uuid.uuid4())[:8],
                collection_site=rec.get("collection_site", "UNKNOWN"),
                shift=rec.get("shift", "DAY"),
                hil_h=float(rec.get("hil_h", 0)),
                hil_i=float(rec.get("hil_i", 0)),
                hil_l=float(rec.get("hil_l", 0)),
                collection_date=rec.get("collection_date", ""),
                accession_id=rec.get("accession_id", ""),
                phlebotomist_id=rec.get("phlebotomist_id", ""),
            )
            self.readings.append(reading)
            count += 1
        return count

    def _compute_stats(self, values: List[float], hil_type: str) -> SiteShiftStatistics:
        """Compute descriptive statistics for a list of values."""
        if not values:
            return SiteShiftStatistics(
                collection_site="", shift="", hil_type=hil_type,
                count=0, mean=0, median=0, p95=0, min_val=0, max_val=0, std_dev=0, flag_rate=0
            )

        n = len(values)
        sorted_vals = sorted(values)
        mean_val = sum(values) / n
        median_val = sorted_vals[n // 2] if n % 2 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
        p95_idx = min(int(math.ceil(0.95 * n)) - 1, n - 1)
        p95_val = sorted_vals[p95_idx]
        variance = sum((x - mean_val) ** 2 for x in values) / max(n - 1, 1)
        std_dev = math.sqrt(variance)

        threshold = self.thresholds.get(hil_type, 100)
        flag_count = sum(1 for v in values if v > threshold)
        flag_rate = (flag_count / n) * 100 if n > 0 else 0

        return SiteShiftStatistics(
            collection_site="", shift="", hil_type=hil_type,
            count=n, mean=round(mean_val, 2), median=round(median_val, 2),
            p95=round(p95_val, 2), min_val=round(min(values), 2),
            max_val=round(max(values), 2), std_dev=round(std_dev, 2),
            flag_rate=round(flag_rate, 2),
        )

    def get_site_shift_distributions(self) -> Dict[str, Dict[str, Dict[str, SiteShiftStatistics]]]:
        """
        Compute per-site/shift distributions for each HIL index type.

        Returns:
            Nested dict: site -> shift -> hil_type -> SiteShiftStatistics
        """
        buckets: Dict[str, Dict[str, Dict[str, List[float]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )

        for r in self.readings:
            buckets[r.collection_site][r.shift]["H"].append(r.hil_h)
            buckets[r.collection_site][r.shift]["I"].append(r.hil_i)
            buckets[r.collection_site][r.shift]["L"].append(r.hil_l)

        result = {}
        for site, shifts in buckets.items():
            result[site] = {}
            for shift, hil_types in shifts.items():
                result[site][shift] = {}
                for hil_type, values in hil_types.items():
                    stats = self._compute_stats(values, hil_type)
                    stats.collection_site = site
                    stats.shift = shift
                    result[site][shift][hil_type] = stats

        return result

    def generate_trend_report(
        self,
        period_start: Optional[str] = None,
        period_end: Optional[str] = None,
    ) -> TrendReport:
        """
        Generate a comprehensive trend report for HIL indices.

        Args:
            period_start: ISO date string for report start
            period_end: ISO date string for report end

        Returns:
            TrendReport with statistics and outlier analysis
        """
        filtered = self.readings
        if period_start:
            filtered = [r for r in filtered if r.collection_date >= period_start]
        if period_end:
            filtered = [r for r in filtered if r.collection_date <= period_end]

        distributions = self.get_site_shift_distributions()

        all_stats = []
        outlier_sites = []

        for site, shifts in distributions.items():
            for shift, hil_types in shifts.items():
                for hil_type, stats in hil_types.items():
                    all_stats.append(stats)
                    # Flag sites with flag rates above 20%
                    if stats.flag_rate > 20:
                        outlier_sites.append({
                            "collection_site": site,
                            "shift": shift,
                            "hil_type": hil_type,
                            "flag_rate": stats.flag_rate,
                            "count": stats.count,
                            "severity": "HIGH" if stats.flag_rate > 40 else "MODERATE",
                        })

        return TrendReport(
            report_id=str(uuid.uuid4())[:8],
            period_start=period_start or "ALL",
            period_end=period_end or "ALL",
            total_readings=len(filtered),
            site_shift_stats=all_stats,
            outlier_sites=outlier_sites,
        )

    def get_box_plot_data(self, site: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate box plot data for visualization.

        Args:
            site: Optional filter by collection site

        Returns:
            Dict with box plot data per site/shift
        """
        distributions = self.get_site_shift_distributions()
        plot_data = {}

        for s, shifts in distributions.items():
            if site and s != site:
                continue
            for shift, hil_types in shifts.items():
                key = f"{s}|{shift}"
                plot_data[key] = {}
                for hil_type, stats in hil_types.items():
                    plot_data[key][hil_type] = {
                        "min": stats.min_val,
                        "q1": stats.median - stats.std_dev * 0.5,
                        "median": stats.median,
                        "q3": stats.median + stats.std_dev * 0.5,
                        "max": stats.max_val,
                        "mean": stats.mean,
                        "p95": stats.p95,
                    }

        return plot_data


def main():
    """CLI entry point for HIL trend tracker."""
    import argparse

    parser = argparse.ArgumentParser(description="HIL Trend Tracker")
    parser.add_argument("--input", type=str, help="Input CSV file with HIL readings")
    parser.add_argument("--site", type=str, help="Filter by collection site")
    parser.add_argument("--period-start", type=str, help="Report period start (YYYY-MM-DD)")
    parser.add_argument("--period-end", type=str, help="Report period end (YYYY-MM-DD)")
    parser.add_argument("--box-plot", action="store_true", help="Output box plot data")
    args = parser.parse_args()

    tracker = HILTrendTracker()

    if args.input:
        import csv as csv_mod
        with open(args.input, "r") as f:
            reader = csv_mod.DictReader(f)
            records = list(reader)
            count = tracker.ingest_batch(records)
            print(f"Ingested {count} readings")

    if args.box_plot:
        data = tracker.get_box_plot_data(site=args.site)
        print(json.dumps(data, indent=2, default=str))
    else:
        report = tracker.generate_trend_report(
            period_start=args.period_start,
            period_end=args.period_end,
        )
        print(json.dumps(report.to_dict(), indent=2, default=str))


if __name__ == "__main__":
    main()
