from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Answer, AnswerLike, Profile, Question, QuestionLike, Tag


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0
    fk_name = "user"


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    raw_id_fields = ("author",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug")
    search_fields = ("name", "slug")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "rating", "created_at")
    search_fields = ("title", "text", "author__username")
    list_filter = ("created_at", "tags")
    raw_id_fields = ("author",)
    inlines = (AnswerInline,)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "author", "rating", "is_correct", "created_at")
    search_fields = ("text", "author__username", "question__title")
    list_filter = ("is_correct", "created_at")
    raw_id_fields = ("author", "question")


@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "question", "value", "created_at")
    search_fields = ("user__username", "question__title")
    list_filter = ("value", "created_at")
    raw_id_fields = ("user", "question")


@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "answer", "value", "created_at")
    search_fields = ("user__username", "answer__text")
    list_filter = ("value", "created_at")
    raw_id_fields = ("user", "answer")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "avatar")
    search_fields = ("user__username", "user__email")
    raw_id_fields = ("user",)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
