from django.db import models
from django.contrib.auth.models import User


class Salesperson(models.Model):
    """
    Represents a salesperson who is also a Django user.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="salesperson_profile"
    )
    employee_id = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"


class Customer(models.Model):
    """
    A customer company (organization). Users may belong to multiple customers.
    """
    customer_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)

    # optional but often needed: who owns this customer
    primary_salesperson = models.ForeignKey(
        Salesperson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_customers"
    )

    def __str__(self):
        return f"{self.customer_number} — {self.name}"


class CustomerMembership(models.Model):
    """
    A user belonging to a customer (a company).
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="customer_memberships"
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="members"
    )

    # optional: useful for permissions/roles
    role = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        unique_together = ("user", "customer")

    def __str__(self):
        return f"{self.user.username} → {self.customer.customer_number}"
