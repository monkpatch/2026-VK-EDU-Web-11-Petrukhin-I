import uuid
from pathlib import Path

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count
from django.urls import reverse


class QuestionQuerySet(models.QuerySet):
    def with_related(self):
        return self.select_related("author__profile").prefetch_related("tags").annotate(answers_count=Count("answers"))

    def new(self):
        return self.with_related().order_by("-created_at")

    def hot(self):
        return self.with_related().order_by("-rating", "-created_at")

    def by_tag(self, tag_name):
        return self.with_related().filter(tags__slug=tag_name).order_by("-created_at")


class QuestionManager(models.Manager):
    def get_queryset(self):
        return QuestionQuerySet(self.model, using=self._db)

    def with_related(self):
        return self.get_queryset().with_related()

    def new(self):
        return self.get_queryset().new()

    def hot(self):
        return self.get_queryset().hot()

    def by_tag(self, tag_name):
        return self.get_queryset().by_tag(tag_name)


class Tag(models.Model):
    name = models.CharField("название", max_length=64, unique=True)
    slug = models.SlugField("slug", max_length=64, unique=True)

    class Meta:
        verbose_name = "тег"
        verbose_name_plural = "теги"

    def __str__(self):
        return self.name


def avatar_upload_to(instance, filename):
    ext = Path(filename).suffix.lower()
    return f"avatars/{uuid.uuid4().hex}{ext}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile", verbose_name="пользователь")
    avatar = models.ImageField("аватар", upload_to=avatar_upload_to, blank=True, null=True)

    class Meta:
        verbose_name = "профиль"
        verbose_name_plural = "профили"

    def __str__(self):
        return f"Profile({self.user.username})"


class Question(models.Model):
    title = models.CharField("заголовок", max_length=255)
    text = models.TextField("текст")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="questions", verbose_name="автор")
    tags = models.ManyToManyField(Tag, related_name="questions", verbose_name="теги", blank=True)
    created_at = models.DateTimeField("создан", auto_now_add=True)
    rating = models.IntegerField("рейтинг", default=0)

    objects = QuestionManager()

    class Meta:
        verbose_name = "вопрос"
        verbose_name_plural = "вопросы"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("question", kwargs={"question_id": self.id})


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers", verbose_name="вопрос")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="answers", verbose_name="автор")
    text = models.TextField("текст")
    created_at = models.DateTimeField("создан", auto_now_add=True)
    rating = models.IntegerField("рейтинг", default=0)
    is_correct = models.BooleanField("правильный", default=False)

    class Meta:
        verbose_name = "ответ"
        verbose_name_plural = "ответы"
        ordering = ["created_at"]

    def __str__(self):
        return f"Answer #{self.id} to {self.question_id}"


class QuestionLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="question_likes", verbose_name="пользователь")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="likes", verbose_name="вопрос")
    value = models.SmallIntegerField("значение", default=1)
    created_at = models.DateTimeField("создан", auto_now_add=True)

    class Meta:
        verbose_name = "лайк вопроса"
        verbose_name_plural = "лайки вопросов"
        constraints = [
            models.UniqueConstraint(fields=["user", "question"], name="unique_question_like"),
        ]


class AnswerLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="answer_likes", verbose_name="пользователь")
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name="likes", verbose_name="ответ")
    value = models.SmallIntegerField("значение", default=1)
    created_at = models.DateTimeField("создан", auto_now_add=True)

    class Meta:
        verbose_name = "лайк ответа"
        verbose_name_plural = "лайки ответов"
        constraints = [
            models.UniqueConstraint(fields=["user", "answer"], name="unique_answer_like"),
        ]
