from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required

from .models import Salesperson, Customer, UserProxy

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # If user has proxies (i.e., salesperson or proxy), send to select-customer
            from .models import UserProxy
            has_proxies = UserProxy.objects.filter(user=user).exists()
            if has_proxies:
                # if only 1 proxy, we could auto-select; but you said salesperson must pick -> redirect to selection
                return redirect("accounts:select_customer")
            # otherwise standard landing
            return redirect("products:landing")
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    return redirect("accounts:login")

@login_required
def select_customer(request):
    """
    Render page where a salesperson picks a customer to act as.
    """
    # proxies are UserProxy objects linking user -> customer
    proxies = UserProxy.objects.filter(user=request.user).select_related("customer")

    customers = [p.customer for p in proxies]

    return render(request, "accounts/select_customer.html", {"customers": customers})

@login_required
def set_customer(request):
    """
    POST endpoint to set the current acting customer in session.
    """
    if request.method != "POST":
        return redirect("accounts:select_customer")

    customer_id = request.POST.get("customer_id") or request.POST.get("customer")
    next_url = request.POST.get("next") or request.GET.get("next")

    if not customer_id:
        messages.error(request, "No customer selected.")
        return redirect("accounts:select_customer")

    # make sure the logged-in user is allowed to act as this customer
    allowed = UserProxy.objects.filter(user=request.user, customer_id=customer_id).exists()
    if not allowed:
        messages.error(request, "You are not allowed to act as that customer.")
        return redirect("accounts:select_customer")

    # Persist to session
    request.session["acting_customer_id"] = int(customer_id)  # store as int for convenience
    request.session.modified = True

    messages.success(request, "You are now working as the selected customer.")

    # Redirect: prefer next_url (if safe), else landing
    if next_url:
        return redirect(next_url)
    return redirect("products:landing")

def salesperson_logout(request):
    logout(request)
    return redirect("accounts:login")
