# configurations/views.py
from django.shortcuts import render

def summary(request):
    return render(request, "configurations/summary.html")
