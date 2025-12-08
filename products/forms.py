# products/forms.py
from django import forms
from configurations.models import ProductConfiguration

class ConfigurationForm(forms.ModelForm):
    class Meta:
        model = ProductConfiguration
        fields = "__all__"
