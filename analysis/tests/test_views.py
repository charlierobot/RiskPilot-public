from django.test import TestCase
from django.urls import reverse

from analysis.models import Analysis, DatasetUpload
from analysis.services.analyzer import create_analysis
from django.core.files.uploadedfile import SimpleUploadedFile


class ViewTests(TestCase):
    def test_empty_dashboard_shows_start_action(self):
        response = self.client.get(reverse("analysis:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Inizia con il dataset demo")

    def test_upload_page_is_available(self):
        response = self.client.get(reverse("analysis:upload"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Carica un dataset")

    def test_report_filters_by_level(self):
        file = SimpleUploadedFile(
            "demo.csv",
            b"transaction_id,date,amount,vendor,country,approved_by,category\nTX-1,2026-09-01,100,Vendor,IT,User,Travel\nTX-2,2026-09-05,12000,Vendor,RU,pending,cash\n",
            content_type="text/csv",
        )
        analysis = create_analysis(file)
        response = self.client.get(reverse("analysis:report", args=[analysis.id]), {"level": "high"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TX-2")
        self.assertNotContains(response, "TX-1")
