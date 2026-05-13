from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from pages.views import sidebar_context

from .forms import LoginForm, ProfileForm, SignupForm


def safe_next_url(request):
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return reverse("index")


def render_core(request, template_name, title, **context):
    payload = {"page_title": title, **sidebar_context(), **context}
    return render(request, template_name, payload)


def login(request):
    if request.user.is_authenticated:
        return redirect(safe_next_url(request))
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect(safe_next_url(request))
    else:
        form = LoginForm(request)
    return render_core(request, "core/login.html", "Log In", form=form, next_url=request.GET.get("next", ""))


def signup(request):
    if request.user.is_authenticated:
        return redirect("index")
    if request.method == "POST":
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect("index")
    else:
        form = SignupForm()
    return render_core(request, "core/signup.html", "Registration", form=form)


@require_POST
def logout(request):
    next_url = safe_next_url(request)
    auth_logout(request)
    return redirect(next_url)


@login_required
def profile(request):
    profile_obj = getattr(request.user, "profile", None)
    initial = {
        "email": request.user.email,
        "username": request.user.username,
        "nickname": request.user.first_name,
        "avatar": profile_obj.avatar if profile_obj else None,
    }
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль сохранён.")
            return redirect("profile")
    else:
        form = ProfileForm(initial=initial, user=request.user)
    return render_core(request, "core/profile.html", f"Settings: {request.user.username}", form=form)
