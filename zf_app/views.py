from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def root_redirect(request):
    """
    Smart root dispatcher.
    """
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    if request.session.get("acting_customer_id"):
        return redirect("dashboard:home")

    # Logged in but no customer yet
    return redirect("accounts:select_customer")