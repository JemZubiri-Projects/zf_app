# zf_app/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("config/", include("configurations.urls")),
    path("accounts/", include("accounts.urls")),
    path("products/", include("products.urls", namespace="products")),
    path("dashboard/", include("dashboard.urls", namespace="dashboard")),
]
