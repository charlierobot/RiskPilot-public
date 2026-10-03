import json
from django.db import models


class DatasetUpload(models.Model):
    STATUS_CHOICES = [("valid", "Valido"), ("invalid", "Non valido")]

    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    row_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="valid")
    validation_errors = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.filename} ({self.status})"


class Analysis(models.Model):
    upload = models.OneToOneField(DatasetUpload, on_delete=models.CASCADE, related_name="analysis")
    created_at = models.DateTimeField(auto_now_add=True)
    total_records = models.PositiveIntegerField(default=0)
    high_risk_count = models.PositiveIntegerField(default=0)
    medium_risk_count = models.PositiveIntegerField(default=0)
    low_risk_count = models.PositiveIntegerField(default=0)
    anomaly_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    @property
    def risk_percentage(self):
        if not self.total_records:
            return 0
        return round((self.high_risk_count / self.total_records) * 100)

    def __str__(self):
        return f"Analisi #{self.pk} — {self.upload.filename}"


class RiskRecord(models.Model):
    RISK_LEVELS = [("low", "Basso"), ("medium", "Medio"), ("high", "Alto")]

    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name="records")
    transaction_id = models.CharField(max_length=100)
    date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    vendor = models.CharField(max_length=255)
    country = models.CharField(max_length=2)
    approved_by = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    risk_score = models.PositiveIntegerField(default=0)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS, default="low")
    reasons = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-risk_score", "transaction_id"]
        constraints = [
            models.UniqueConstraint(fields=["analysis", "transaction_id"], name="unique_record_per_analysis")
        ]

    @property
    def reasons_text(self):
        return ", ".join(self.reasons) if self.reasons else "Nessun segnale rilevante"

    def __str__(self):
        return f"{self.transaction_id} — {self.risk_level}"
