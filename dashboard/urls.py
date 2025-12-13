from django.urls import path
from .views import dashboard_home, inbox_view, outbox_view, applications_view

app_name = "dashboard"

urlpatterns = [
    path("", dashboard_home, name="home"),
    path("applications/", applications_view, name="applications"),
    path("inbox/", inbox_view, name="inbox"),
    path("outbox/", outbox_view, name="outbox"),
]
