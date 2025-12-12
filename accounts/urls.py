from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("select-customer/", views.select_customer, name="select_customer"),
    path("set-customer/", views.set_customer, name="set_customer"),
]
