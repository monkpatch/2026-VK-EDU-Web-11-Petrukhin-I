from django import forms
from django.db import transaction
from django.utils.text import slugify

from .models import Answer, Question, Tag


class QuestionForm(forms.ModelForm):
    tags = forms.CharField(
        label="Tags",
        required=False,
        help_text="Введите теги через запятую.",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "django, forms, auth"}),
    )

    class Meta:
        model = Question
        fields = ["title", "text", "tags"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "text": forms.Textarea(attrs={"class": "form-control", "rows": 8}),
        }

    def clean_tags(self):
        raw_tags = self.cleaned_data.get("tags", "")
        names = []
        seen = set()
        for item in raw_tags.split(","):
            name = item.strip()
            if not name:
                continue
            key = name.lower()
            if key not in seen:
                seen.add(key)
                names.append(name)
        if len(names) > 5:
            raise forms.ValidationError("Можно указать не больше 5 тегов.")
        for name in names:
            if len(name) > 64:
                raise forms.ValidationError("Тег не должен быть длиннее 64 символов.")
        return names

    @transaction.atomic
    def save(self, author, commit=True):
        question = super().save(commit=False)
        question.author = author
        if commit:
            question.save()
            tag_objects = []
            for name in self.cleaned_data["tags"]:
                base_slug = slugify(name, allow_unicode=True) or name.lower().replace(" ", "-")
                slug = base_slug[:64]
                suffix = 2
                while Tag.objects.filter(slug=slug).exclude(name__iexact=name).exists():
                    tail = f"-{suffix}"
                    slug = f"{base_slug[:64 - len(tail)]}{tail}"
                    suffix += 1
                tag, _ = Tag.objects.get_or_create(slug=slug, defaults={"name": name})
                tag_objects.append(tag)
            question.tags.set(tag_objects)
        return question


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Enter your answer here..."}),
        }

    def clean_text(self):
        text = self.cleaned_data["text"].strip()
        if not text:
            raise forms.ValidationError("Ответ не может быть пустым.")
        return text

    def save(self, author, question, commit=True):
        answer = super().save(commit=False)
        answer.author = author
        answer.question = question
        if commit:
            answer.save()
        return answer
