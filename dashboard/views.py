from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from products.models import Transaction
from accounts.models import Customer


@login_required
def dashboard_home(request):
    return redirect("dashboard:applications")

@login_required
def inbox_view(request):
    customer_id = request.session.get("acting_customer_id")

    if not customer_id:
        messages.error(request, "Please select a customer to continue.")
        return redirect("accounts:select_customer")

    customer = Customer.objects.get(id=customer_id)

    # Tabs: New, Received, Read
    status = request.GET.get("status", "New")

    base_qs = Transaction.objects.filter(
        customer_id=customer_id,
        transaction_type="Inbox",
    ).order_by("-transaction_date", "-id")

    # Status counts (for tabs)
    new_count = base_qs.filter(transaction_status="New").count()
    received_count = base_qs.filter(transaction_status="Received").count()
    read_count = base_qs.filter(transaction_status="Read").count()

    # Messages for selected tab
    inbox_items = base_qs.filter(transaction_status=status)

    context = {
        "customer": customer,
        "inbox_items": inbox_items,
        "status": status,
        "new_count": new_count,
        "received_count": received_count,
        "read_count": read_count,
        "active_section": "inbox",   # sidebar highlight
    }

    return render(request, "dashboard/inbox.html", context)

@login_required
def outbox_view(request):
    customer_id = request.session.get("acting_customer_id")

    if not customer_id:
        messages.error(request, "Please select a customer to continue.")
        return redirect("accounts:select_customer")

    customer = Customer.objects.get(id=customer_id)

    status = request.GET.get("status", "New")

    base_qs = Transaction.objects.filter(
        customer_id=customer_id,
        transaction_type="Outbox",
    ).order_by("-transaction_date", "-id")

    # Status counts (tabs)
    new_count = base_qs.filter(transaction_status="New").count()
    received_count = base_qs.filter(transaction_status="Received").count()
    read_count = base_qs.filter(transaction_status="Read").count()

    # Items for selected tab
    outbox_items = base_qs.filter(transaction_status=status)

    context = {
        "customer": customer,
        "outbox_items": outbox_items,
        "active_section": "outbox",  # highlight sidebar
        "status": status,
        "new_count": new_count,
        "received_count": received_count,
        "read_count": read_count,
    }

    return render(request, "dashboard/outbox.html", context)

@login_required
def applications_view(request):
    customer_id = request.session.get("acting_customer_id")

    if not customer_id:
        messages.error(request, "Please select a customer first.")
        return redirect("accounts:select_customer")

    customer = Customer.objects.get(id=customer_id)

    context = {
        "customer": customer,
        "active_section": "applications",
    }

    return render(request, "dashboard/applications.html", context)

