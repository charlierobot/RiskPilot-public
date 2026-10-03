import json
from pathlib import Path

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import UploadDatasetForm
from .models import Analysis, RiskRecord
from .services.analyzer import AnalysisError, create_analysis


BASE_DIR = Path(__file__).resolve().parent.parent


def dashboard(request):
    analysis = Analysis.objects.first()
    if not analysis:
        return render(request, "analysis/empty_dashboard.html")
    return redirect("analysis:analysis_dashboard", analysis_id=analysis.id)


def upload_dataset(request):
    form = UploadDatasetForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            analysis = create_analysis(form.cleaned_data["dataset"])
        except AnalysisError as exc:
            for error in exc.errors:
                messages.error(request, error)
        else:
            messages.success(request, "Dataset validato e analizzato correttamente.")
            return redirect("analysis:analysis_dashboard", analysis_id=analysis.id)
    return render(request, "analysis/upload.html", {"form": form})


def demo_analysis(request):
    demo_path = BASE_DIR / "sample_data" / "demo_transactions.csv"
    with demo_path.open("rb") as demo_file:
        analysis = create_analysis(demo_file, filename="demo_transactions.csv")
    messages.success(request, "Dataset demo caricato: ora puoi esplorare i segnali di rischio.")
    return redirect("analysis:analysis_dashboard", analysis_id=analysis.id)


def analysis_dashboard(request, analysis_id):
    analysis = get_object_or_404(Analysis, pk=analysis_id)
    high_records = analysis.records.filter(risk_level="high")[:5]
    return render(request, "analysis/dashboard.html", {"analysis": analysis, "high_records": high_records})


def report(request, analysis_id):
    analysis = get_object_or_404(Analysis, pk=analysis_id)
    records = analysis.records.all()
    level = request.GET.get("level", "").lower()
    query = request.GET.get("q", "").strip()
    if level in {"low", "medium", "high"}:
        records = records.filter(risk_level=level)
    if query:
        records = records.filter(transaction_id__icontains=query) | records.filter(vendor__icontains=query)
    paginator = Paginator(records, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "analysis/report.html", {"analysis": analysis, "page_obj": page_obj, "active_level": level, "query": query})


def record_detail(request, analysis_id, record_id):
    analysis = get_object_or_404(Analysis, pk=analysis_id)
    record = get_object_or_404(RiskRecord, pk=record_id, analysis=analysis)
    return render(request, "analysis/record_detail.html", {"analysis": analysis, "record": record})


def route_manifest(request):
    manifest_path = BASE_DIR / "static" / "manus-routes.json"
    with manifest_path.open(encoding="utf-8") as manifest_file:
        return JsonResponse(json.load(manifest_file))
