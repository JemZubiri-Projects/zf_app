# products/urls.py
from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    path("", views.landing, name="landing"),

    path("product/configure/", views.configure_product, name="configure_product"),
    path("product/configure/save/", views.save_configuration, name="save_configuration"),

    path("get-quote/", views.get_quote, name="get_quote"),
]
