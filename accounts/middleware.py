from django.shortcuts import redirect
from django.urls import reverse


class RequireCustomerMiddleware:
    """
    Ensures that authenticated users choose an acting customer,
    but does NOT interfere with login/logout or public paths.
    """

    EXEMPT_URLS = None

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if self.EXEMPT_URLS is None:
            self.EXEMPT_URLS = {
                reverse("accounts:login"),
                reverse("accounts:logout"),
                reverse("accounts:select_customer"),
                reverse("accounts:set_customer"),
                "/admin/",                # prefix check done below
                "/static/",               # prefix check
            }

        path = request.path

        # Allow admin and static files
        if path.startswith("/admin/") or path.startswith("/static/"):
            return self.get_response(request)

        # If the user is not logged in, allow public pages
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Exempt URLs
        if path in self.EXEMPT_URLS:
            return self.get_response(request)

        # If acting customer is not selected → redirect
        if not request.session.get("acting_customer_id"):
            return redirect("accounts:select_customer")

        return self.get_response(request)
