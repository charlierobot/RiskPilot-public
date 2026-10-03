from datetime import date
from decimal import Decimal
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from analysis.models import Analysis, RiskRecord
from analysis.services.analyzer import AnalysisError, create_analysis
from analysis.services.csv_validator import validate_csv
from analysis.services.risk_engine import evaluate_record


VALID_CSV = b"transaction_id,date,amount,vendor,country,approved_by,category\nTX-001,2026-09-01,120.50,Alfa SRL,IT,Mario Rossi,Travel\n"


class CsvValidatorTests(TestCase):
    def test_valid_csv_is_accepted(self):
        file = SimpleUploadedFile("valid.csv", VALID_CSV, content_type="text/csv")
        result = validate_csv(file)
        self.assertTrue(result.valid)
        self.assertEqual(len(result.dataframe), 1)

    def test_missing_column_is_reported(self):
        file = SimpleUploadedFile("invalid.csv", b"transaction_id,amount\nTX-1,10\n", content_type="text/csv")
        result = validate_csv(file)
        self.assertFalse(result.valid)
        self.assertIn("Mancano le colonne obbligatorie", result.errors[0])

    def test_negative_amount_is_rejected(self):
        content = VALID_CSV.replace(b"120.50", b"-5")
        file = SimpleUploadedFile("negative.csv", content, content_type="text/csv")
        result = validate_csv(file)
        self.assertFalse(result.valid)
        self.assertTrue(any("negativi" in error for error in result.errors))


class RiskEngineTests(TestCase):
    def test_high_risk_record_explains_score(self):
        evaluation = evaluate_record(
            amount=Decimal("12000"), country="RU", approved_by="pending", category="cash", record_date=date(2026, 9, 5)
        )
        self.assertEqual(evaluation.level, "high")
        self.assertGreaterEqual(evaluation.score, 60)
        self.assertGreaterEqual(len(evaluation.reasons), 4)

    def test_normal_record_is_low_risk(self):
        evaluation = evaluate_record(
            amount=Decimal("120"), country="IT", approved_by="Mario Rossi", category="Travel", record_date=date(2026, 9, 1)
        )
        self.assertEqual(evaluation.level, "low")
        self.assertEqual(evaluation.score, 0)


class AnalysisFlowTests(TestCase):
    def test_analysis_persists_records_and_counters(self):
        file = SimpleUploadedFile("valid.csv", VALID_CSV, content_type="text/csv")
        analysis = create_analysis(file)
        self.assertEqual(Analysis.objects.count(), 1)
        self.assertEqual(RiskRecord.objects.filter(analysis=analysis).count(), 1)
        self.assertEqual(analysis.low_risk_count, 1)

    def test_invalid_upload_does_not_create_analysis(self):
        file = SimpleUploadedFile("invalid.csv", b"foo,bar\n1,2\n", content_type="text/csv")
        with self.assertRaises(AnalysisError):
            create_analysis(file)
        self.assertEqual(Analysis.objects.count(), 0)
