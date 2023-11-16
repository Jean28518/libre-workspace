from django.shortcuts import render, redirect

# Create your views here.
def welcome_index(request):
    # If request is POST
    message = ""
    if request.method == "POST":
        password = request.POST["password"]
        password_repeat = request.POST["password_repeat"]
        if password.strip() == "":
            message = "Passwort darf nicht leer sein."
        if password == password_repeat:
            request.session["password"] = password
        else:
            message = "Passwörter stimmen nicht überein. Bitte versuchen Sie es erneut."
        if message == "":
            print("Mami")
            return redirect("welcome_select_apps")

    return render(request, "welcome/welcome_index.html", {"message": message})


def welcome_select_apps(request):
    if request.method == "POST":
        request.session["nextcloud"] = request.POST.get("nextcloud", "")
        request.session["onlineoffice"] = request.POST.get("onlineoffice", "")
        request.session["rocketchat"] = request.POST.get("rocketchat", "")
        request.session["jitisi"] = request.POST.get("jitisi", "")
        return redirect("welcome_dns_settings")

    return render(request, "welcome/welcome_select_apps.html")


def welcome_dns_settings(request):
    message = ""
    if request.method == "POST":
        request.session["visibility"] = request.POST.get("visibility", "")
        request.session["domain"] = request.POST.get("domain", "")
        if request.session["visibility"] == "public":
            if request.session["domain"] == "":
                message = "Bitte geben Sie eine Domain an."
            elif request.session["domain"].count(".") != 1:
                message = "Bitte stellen Sie sicher, dass Sie nur die Domain angeben und keine Subdomain."
        if message == "":
            return redirect("welcome_email_settings")
    return render(request, "welcome/welcome_dns_settings.html")


def welcome_email_settings(request):
    if request.method == "POST":
        skip = request.POST.get("skip", "")
        if skip == "":
            request.session["mailhost"] = request.POST.get("mailhost", "")
            request.session["mailport"] = request.POST.get("mailport", "")
            request.session["mailuser"] = request.POST.get("mailuser", "")
            request.session["mailpassword"] = request.POST.get("mailpassword", "")
            request.session["mailencryption"] = request.POST.get("mailencryption", "")
        ## TODO: Start here the installation process
        return redirect("installation_running")
    return render(request, "welcome/welcome_email_settings.html", {"message": ""})


def installation_running(request):
    return render(request, "welcome/installation_running.html")