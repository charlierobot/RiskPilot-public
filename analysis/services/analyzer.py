from __future__ import annotations

from decimal import Decimal

import pandas as pd
from django.db import transaction

from analysis.models import Analysis, DatasetUpload, RiskRecord
from .csv_validator import ValidationResult, validate_csv
from .risk_engine import evaluate_record


class AnalysisError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


@transaction.atomic
def create_analysis(uploaded_file, *, filename: str | None = None) -> Analysis:
    result: ValidationResult = validate_csv(uploaded_file)
    filename = filename or getattr(uploaded_file, "name", "dataset.csv")
    if not result.valid or result.dataframe is None:
        DatasetUpload.objects.create(
            filename=filename,
            row_count=0 if result.dataframe is None else len(result.dataframe),
            status="invalid",
            validation_errors=result.errors,
        )
        raise AnalysisError(result.errors)

    dataframe = result.dataframe
    upload = DatasetUpload.objects.create(
        filename=filename,
        row_count=len(dataframe),
        status="valid",
        validation_errors=result.warnings,
    )
    analysis = Analysis.objects.create(upload=upload, total_records=len(dataframe))

    records = []
    for row in dataframe.to_dict(orient="records"):
        parsed_date = pd.to_datetime(row["date"]).date()
        amount = Decimal(str(row["amount"]))
        evaluation = evaluate_record(
            amount=amount,
            country=str(row["country"]),
            approved_by=str(row["approved_by"]),
            category=str(row["category"]),
            record_date=parsed_date,
        )
        records.append(
            RiskRecord(
                analysis=analysis,
                transaction_id=str(row["transaction_id"]).strip(),
                date=parsed_date,
                amount=amount,
                vendor=str(row["vendor"]).strip(),
                country=str(row["country"]).strip().upper(),
                approved_by=str(row["approved_by"]).strip(),
                category=str(row["category"]).strip(),
                risk_score=evaluation.score,
                risk_level=evaluation.level,
                reasons=evaluation.reasons,
            )
        )

    RiskRecord.objects.bulk_create(records)
    counts = {level: sum(record.risk_level == level for record in records) for level in ("high", "medium", "low")}
    analysis.high_risk_count = counts["high"]
    analysis.medium_risk_count = counts["medium"]
    analysis.low_risk_count = counts["low"]
    analysis.anomaly_count = sum(bool(record.reasons) for record in records)
    analysis.save(update_fields=["high_risk_count", "medium_risk_count", "low_risk_count", "anomaly_count"])
    return analysis
