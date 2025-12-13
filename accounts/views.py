from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Customer, CustomerMembership, Salesperson


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("accounts:select_customer")

        messages.error(request, "Invalid username or password")

    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect("accounts:login")

@login_required
def select_customer(request):
    user = request.user

    # customers from membership
    membership_customers = Customer.objects.filter(
        members__user=user
    )

    # customers from salesperson assignment
    salesperson_customers = Customer.objects.none()
    if hasattr(user, "salesperson_profile"):
        salesperson_customers = Customer.objects.filter(
            primary_salesperson=user.salesperson_profile
        )

    # Combine safely (avoids unique vs non-unique error)
    customers = membership_customers.union(salesperson_customers)

    if not customers.exists():
        messages.error(request, "You are not assigned to any customers.")
        logout(request)
        return redirect("accounts:login")

    return render(request, "accounts/select_customer.html", {"customers": customers})


@login_required
def set_customer(request):
    """
    Saves selected customer to the session, ensuring the user is authorized.
    """
    if request.method != "POST":
        return redirect("accounts:select_customer")

    customer_id = request.POST.get("customer") or request.POST.get("customer_id")
    next_url = request.POST.get("next") or request.GET.get("next")

    if not customer_id:
        messages.error(request, "No customer selected.")
        return redirect("accounts:select_customer")

    user = request.user

    # Check membership
    is_member = CustomerMembership.objects.filter(
        user=user,
        customer_id=customer_id
    ).exists()

    # Check salesperson assignment
    is_salesperson = False
    if hasattr(user, "salesperson_profile"):
        is_salesperson = Customer.objects.filter(
            id=customer_id,
            primary_salesperson=user.salesperson_profile
        ).exists()

    if not (is_member or is_salesperson):
        messages.error(request, "You are not allowed to act as that customer.")
        return redirect("accounts:select_customer")

    # Store
    request.session["acting_customer_id"] = int(customer_id)
    request.session.modified = True

    messages.success(request, "You are now working as the selected customer.")

    return redirect("dashboard:home")
