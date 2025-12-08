# products/urls.py
from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    path("", views.home, name="home"),
    path("landing/", views.landing, name="landing"),
    path("logout/", views.logout_view, name="logout"),

    path("product/configure/", views.configure_product, name="configure_product"),
    path("product/configure/save/", views.save_configuration, name="save_configuration"),

    path("api/transmission/", views.api_transmission_by_duty, name="api_transmission"),
    path("get-quote/", views.get_quote, name="get_quote"),
]
