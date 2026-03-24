from django.shortcuts import render


def page(request, template_name, title, auth=True):
    return render(request, template_name, {"page_title": title, "auth": auth})


def index(request):
    return page(request, "pages/index.html", "New Questions", auth=True)


def hot(request):
    return page(request, "pages/hot.html", "Hot Questions", auth=True)


def tag(request):
    return page(request, "pages/tag.html", "Tag: black-jack", auth=False)


def question(request):
    return page(request, "pages/question.html", "How to build a moon park ?", auth=False)


def ask(request):
    return page(request, "pages/ask.html", "New Question", auth=False)


def login(request):
    return page(request, "pages/login.html", "Log In", auth=False)


def signup(request):
    return page(request, "pages/signup.html", "Registration", auth=False)


def profile(request):
    return page(request, "pages/profile.html", "Settings: Dr. Pepper", auth=True)
