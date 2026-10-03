from django.contrib import admin
from .models import Analysis, DatasetUpload, RiskRecord


@admin.register(DatasetUpload)
class DatasetUploadAdmin(admin.ModelAdmin):
    list_display = ("filename", "uploaded_at", "row_count", "status")
    list_filter = ("status",)


@admin.register(Analysis)
class AnalysisAdmin(admin.ModelAdmin):
    list_display = ("id", "upload", "created_at", "total_records", "high_risk_count")


@admin.register(RiskRecord)
class RiskRecordAdmin(admin.ModelAdmin):
    list_display = ("transaction_id", "analysis", "amount", "risk_score", "risk_level")
    list_filter = ("risk_level", "country", "category")
    search_fields = ("transaction_id", "vendor")
