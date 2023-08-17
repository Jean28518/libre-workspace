from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
import django_auth_ldap.backend

def signal_handler(context, user, request, exception, **kwargs):
    print("Context: " + str(context) + "\nUser: " + str(user) + "\nRequest: " + str(request) + "\nException: " + str(exception))

django_auth_ldap.backend.ldap_error.connect(signal_handler)





# Create your views here.
def index(request):
    if request.user.is_authenticated:
        return render(request, "idm/index.html", {"request": request})
    print("21")
    return redirect(user_login)

def user_login(request):
    if request.user.is_authenticated:
        return redirect(index)
    if request.method == 'POST':
        user = authenticate(username=request.POST['username'], password=request.POST['password'])
        if user and user.is_authenticated:
            print("User is authenticated")
            login(request, user)
            # if request.GET.get("next", "") != "":
            #     return HttpResponseRedirect(request.GET['next'])
            # else: 
            return redirect(index)
        else:
            print("User is not authenticated")
            return render(request, 'idm/login.html', {'error_message': "Anmeldung fehlgeschlagen! Bitte versuchen Sie es erneut."})
    return render(request, "idm/login.html", {"request": request})

def user_logout(request):
    logout(request)
    return redirect(index)


def user_password_reset(request):
    return render(request, "idm/login.html")