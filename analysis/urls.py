from django.urls import path
from . import views

app_name = "analysis"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("manus-routes.json", views.route_manifest, name="route_manifest"),
    path("upload/", views.upload_dataset, name="upload"),
    path("demo/", views.demo_analysis, name="demo"),
    path("analysis/<int:analysis_id>/", views.analysis_dashboard, name="analysis_dashboard"),
    path("analysis/<int:analysis_id>/report/", views.report, name="report"),
    path("analysis/<int:analysis_id>/record/<int:record_id>/", views.record_detail, name="record_detail"),
]
