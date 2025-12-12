from django.shortcuts import redirect

class RequireCustomerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Only enforce for authenticated salespeople
        user = request.user

        if user.is_authenticated and hasattr(user, "salesperson_profile"):
            if not request.session.get("acting_customer_id"):
                # Skip enforcement for login + customer selection routes
                if not request.path.startswith("/accounts/select-customer") and \
                   not request.path.startswith("/accounts/set-customer"):
                    return redirect("accounts:select_customer")

        return self.get_response(request)
