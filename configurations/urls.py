# configurations/urls.py
from django.urls import path
from . import views

app_name = "configurations"

urlpatterns = [
    path("", views.summary, name="summary"),
]