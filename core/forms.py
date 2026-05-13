from django import forms
from django.contrib.auth import authenticate, get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.db import transaction

from pages.models import Profile

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Login",
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "username"}),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "current-password"}),
    )


class SignupForm(forms.Form):
    username = forms.CharField(
        label="Login",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "username"}),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
    )
    nickname = forms.CharField(
        label="NickName",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "name"}),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )
    password_repeat = forms.CharField(
        label="Repeat password",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )
    avatar = forms.URLField(
        label="Avatar URL",
        required=False,
        widget=forms.URLInput(attrs={"class": "form-control", "placeholder": "https://example.com/avatar.jpg"}),
    )

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("Пользователь с таким логином уже существует.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Этот email уже зарегистрирован.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_repeat = cleaned_data.get("password_repeat")
        if password and password_repeat and password != password_repeat:
            self.add_error("password_repeat", "Пароли не совпадают.")
        if password:
            user = User(
                username=cleaned_data.get("username") or "",
                email=cleaned_data.get("email") or "",
                first_name=cleaned_data.get("nickname") or "",
            )
            try:
                password_validation.validate_password(password, user)
            except ValidationError as error:
                self.add_error("password", error)
        return cleaned_data

    @transaction.atomic
    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password"],
            first_name=self.cleaned_data.get("nickname", ""),
        )
        Profile.objects.create(user=user, avatar=self.cleaned_data.get("avatar", ""))
        return user


class ProfileForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
    )
    username = forms.CharField(
        label="Login",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "username"}),
    )
    nickname = forms.CharField(
        label="NickName",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "autocomplete": "name"}),
    )
    avatar = forms.URLField(
        label="Avatar URL",
        required=False,
        widget=forms.URLInput(attrs={"class": "form-control", "placeholder": "https://example.com/avatar.jpg"}),
    )

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exclude(pk=self.user.pk).exists():
            raise ValidationError("Пользователь с таким логином уже существует.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise ValidationError("Этот email уже используется другим пользователем.")
        return email

    @transaction.atomic
    def save(self):
        self.user.email = self.cleaned_data["email"]
        self.user.username = self.cleaned_data["username"]
        self.user.first_name = self.cleaned_data.get("nickname", "")
        self.user.save(update_fields=["email", "username", "first_name"])
        profile, _ = Profile.objects.get_or_create(user=self.user)
        profile.avatar = self.cleaned_data.get("avatar", "")
        profile.save(update_fields=["avatar"])
        return self.user
