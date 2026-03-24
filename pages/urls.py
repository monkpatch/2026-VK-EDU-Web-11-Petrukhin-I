from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("hot/", views.hot, name="hot"),
    path("tag/", views.tag, name="tag"),
    path("question/", views.question, name="question"),
    path("ask/", views.ask, name="ask"),
    path("login/", views.login, name="login"),
    path("signup/", views.signup, name="signup"),
    path("profile/", views.profile, name="profile"),
]
