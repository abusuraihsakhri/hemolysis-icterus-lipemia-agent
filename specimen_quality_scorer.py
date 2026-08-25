#!/usr/bin/env python3
"""
Specimen Quality Scorer: Automated Specimen Quality Score (SQS)
Computes a composite quality score from multiple pre-analytical factors
including HIL interference, collection-to-centrifugation time, and storage conditions.

Domain: Laboratory Medicine — Pre-Analytical Quality
Author: Dr. Abu Suraih Sakhri
License: MIT
"""

import datetime
import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional


@dataclass
class SpecimenQualityAssessment:
    """Complete specimen quality assessment result."""
    assessment_id: str
    accession_id: str
    sqs_score: float  # 0-100 composite score
    hil_penalty: float
    time_penalty: float
    storage_penalty: float
    quality_grade: str  # EXCELLENT, GOOD, ACCEPTABLE, MARGINAL, REJECTED
    flags: List[str]
    recommendations: List[str]
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SpecimenMetadata:
    """Metadata for a specimen being assessed."""
    accession_id: str
    collection_timestamp: str
    centrifugation_timestamp: Optional[str] = None
    hil_h: float = 0.0
    hil_i: float = 0.0
    hil_l: float = 0.0
    storage_temp_celsius: Optional[float] = None
    temp_excursion_minutes: float = 0.0
    specimen_type: str = "serum"
    analytes_requested: List[str] = field(default_factory=list)


# Analyte-specific collection-to-centrifugation thresholds (minutes)
CENTRIFUGATION_THRESHOLDS: Dict[str, float] = {
    "GLUC": 30,      # Glucose: 30 min
    "K": 60,         # Potassium: 60 min
    "LDH": 60,       # LDH: 60 min
    "NH3": 30,       # Ammonia: 30 min
    "LACTATE": 15,   # Lactate: 15 min
    "DEFAULT": 120,  # Default: 2 hours
}

# HIL penalty thresholds
HIL_PENALTY_TIERS = [
    (50, 0),      # 0-50: no penalty
    (100, 10),    # 51-100: minor penalty
    (200, 25),    # 101-200: moderate penalty
    (500, 50),    # 201-500: significant penalty
    (1000, 80),   # 501-1000: severe penalty
]

# Storage temperature ranges (Celsius)
STORAGE_TEMP_RANGES = {
    "serum": (2, 8),
    "plasma": (2, 8),
    "whole_blood": (20, 25),  # Room temperature
    "urine": (2, 8),
    "csf": (2, 8),
}


class SpecimenQualityScorer:
    """
    Computes a composite Specimen Quality Score (SQS) from multiple
    pre-analytical factors.
    """

    def __init__(
        self,
        hil_weight: float = 0.40,
        time_weight: float = 0.30,
        storage_weight: float = 0.30,
    ):
        self.hil_weight = hil_weight
        self.time_weight = time_weight
        self.storage_weight = storage_weight

    def _compute_hil_penalty(self, hil_h: float, hil_i: float, hil_l: float) -> float:
        """Compute HIL penalty score (0-100, higher = worse)."""
        penalties = []
        for hil_val in [hil_h, hil_i, hil_l]:
            penalty = 0
            for threshold, pen in HIL_PENALTY_TIERS:
                if hil_val <= threshold:
                    penalty = pen
                    break
            else:
                penalty = 100
            penalties.append(penalty)
        return max(penalties)  # Use worst HIL penalty

    def _compute_time_penalty(
        self,
        collection_ts: str,
        centrifugation_ts: Optional[str],
        analytes: List[str],
    ) -> float:
        """Compute time-based penalty for collection-to-centrifugation interval."""
        if not centrifugation_ts or not collection_ts:
            return 0.0

        try:
            coll_dt = datetime.datetime.fromisoformat(collection_ts.replace("Z", "+00:00"))
            cent_dt = datetime.datetime.fromisoformat(centrifugation_ts.replace("Z", "+00:00"))
            interval_minutes = (cent_dt - coll_dt).total_seconds() / 60
        except (ValueError, TypeError):
            return 0.0

        if interval_minutes < 0:
            return 10.0  # Clock skew penalty

        # Find most restrictive threshold for requested analytes
        min_threshold = CENTRIFUGATION_THRESHOLDS["DEFAULT"]
        for analyte in analytes:
            threshold = CENTRIFUGATION_THRESHOLDS.get(analyte.upper(), CENTRIFUGATION_THRESHOLDS["DEFAULT"])
            min_threshold = min(min_threshold, threshold)

        if interval_minutes <= min_threshold:
            return 0.0
        elif interval_minutes <= min_threshold * 2:
            return 25.0
        elif interval_minutes <= min_threshold * 4:
            return 50.0
        else:
            return 80.0

    def _compute_storage_penalty(
        self,
        specimen_type: str,
        storage_temp: Optional[float],
        temp_excursion_minutes: float,
    ) -> float:
        """Compute storage condition penalty."""
        penalty = 0.0

        if storage_temp is not None:
            lo, hi = STORAGE_TEMP_RANGES.get(specimen_type.lower(), (2, 8))
            if storage_temp < lo:
                deviation = lo - storage_temp
                penalty += min(deviation * 10, 60)
            elif storage_temp > hi:
                deviation = storage_temp - hi
                penalty += min(deviation * 10, 60)

        if temp_excursion_minutes > 0:
            if temp_excursion_minutes > 60:
                penalty += 40
            elif temp_excursion_minutes > 30:
                penalty += 20
            elif temp_excursion_minutes > 10:
                penalty += 10

        return min(penalty, 100)

    def assess_specimen(self, specimen: SpecimenMetadata) -> SpecimenQualityAssessment:
        """
        Compute composite SQS for a specimen.

        Args:
            specimen: SpecimenMetadata with collection details

        Returns:
            SpecimenQualityAssessment with SQS score and breakdown
        """
        hil_penalty = self._compute_hil_penalty(specimen.hil_h, specimen.hil_i, specimen.hil_l)
        time_penalty = self._compute_time_penalty(
            specimen.collection_timestamp,
            specimen.centrifugation_timestamp,
            specimen.analytes_requested,
        )
        storage_penalty = self._compute_storage_penalty(
            specimen.specimen_type,
            specimen.storage_temp_celsius,
            specimen.temp_excursion_minutes,
        )

        # Composite SQS: 100 = perfect, 0 = worst
        sqs = 100 - (
            hil_penalty * self.hil_weight +
            time_penalty * self.time_weight +
            storage_penalty * self.storage_weight
        )
        sqs = max(0, min(100, sqs))

        # Quality grade
        if sqs >= 90:
            grade = "EXCELLENT"
        elif sqs >= 75:
            grade = "GOOD"
        elif sqs >= 60:
            grade = "ACCEPTABLE"
        elif sqs >= 40:
            grade = "MARGINAL"
        else:
            grade = "REJECTED"

        flags = []
        recommendations = []

        if hil_penalty > 25:
            flags.append(f"HIL interference detected (penalty: {hil_penalty:.0f})")
            recommendations.append("Consider specimen recollection or corrected values")
        if time_penalty > 25:
            flags.append(f"Collection-to-centrifugation interval exceeded threshold (penalty: {time_penalty:.0f})")
            recommendations.append("Review specimen handling protocols")
        if storage_penalty > 25:
            flags.append(f"Storage condition deviation detected (penalty: {storage_penalty:.0f})")
            recommendations.append("Verify storage temperature compliance")
        if sqs < 40:
            flags.append("SQS below acceptable threshold — specimen may be unsuitable for testing")
            recommendations.append("Recommend recollection")

        return SpecimenQualityAssessment(
            assessment_id=str(uuid.uuid4())[:8],
            accession_id=specimen.accession_id,
            sqs_score=round(sqs, 2),
            hil_penalty=round(hil_penalty, 2),
            time_penalty=round(time_penalty, 2),
            storage_penalty=round(storage_penalty, 2),
            quality_grade=grade,
            flags=flags,
            recommendations=recommendations,
        )

    def batch_assess(self, specimens: List[SpecimenMetadata]) -> List[SpecimenQualityAssessment]:
        """Assess multiple specimens."""
        return [self.assess_specimen(s) for s in specimens]


def main():
    """CLI entry point for specimen quality scorer."""
    import argparse

    parser = argparse.ArgumentParser(description="Specimen Quality Scorer")
    parser.add_argument("--accession", type=str, required=True, help="Accession ID")
    parser.add_argument("--hil-h", type=float, default=0, help="Hemolysis index")
    parser.add_argument("--hil-i", type=float, default=0, help="Icterus index")
    parser.add_argument("--hil-l", type=float, default=0, help="Lipemia index")
    parser.add_argument("--collection-time", type=str, required=True, help="Collection timestamp (ISO)")
    parser.add_argument("--centrifugation-time", type=str, help="Centrifugation timestamp (ISO)")
    parser.add_argument("--storage-temp", type=float, help="Storage temperature (Celsius)")
    parser.add_argument("--specimen-type", type=str, default="serum", help="Specimen type")
    args = parser.parse_args()

    scorer = SpecimenQualityScorer()
    specimen = SpecimenMetadata(
        accession_id=args.accession,
        collection_timestamp=args.collection_time,
        centrifugation_timestamp=args.centrifugation_time,
        hil_h=args.hil_h,
        hil_i=args.hil_i,
        hil_l=args.hil_l,
        storage_temp_celsius=args.storage_temp,
        specimen_type=args.specimen_type,
    )

    result = scorer.assess_specimen(specimen)
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
