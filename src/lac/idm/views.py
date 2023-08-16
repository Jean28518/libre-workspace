from django.shortcuts import render, redirect
from django.http import HttpResponse


# Create your views here.
def index(request):
    return redirect(login)

def login(request):
    return render(request, "idm/login.html")


def password_reset(request):
    return render(request, "idm/login.html")