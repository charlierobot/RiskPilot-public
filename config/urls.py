from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("analysis.urls")),
]

urlpatterns += staticfiles_urlpatterns()
