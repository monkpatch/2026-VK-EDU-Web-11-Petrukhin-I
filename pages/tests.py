import json
import shutil
import tempfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import connection
from django.test import RequestFactory, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from .models import Answer, AnswerLike, Profile, Question, QuestionLike, Tag
from .views import paginate, sidebar_context


class PagesRoutingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", email="tester@example.com", password="StrongPass123")
        Profile.objects.create(user=self.user)
        self.tag = Tag.objects.create(name="django", slug="django")
        for i in range(1, 25):
            q = Question.objects.create(
                title=f"Question {i}",
                text="Some text",
                author=self.user,
                rating=i,
            )
            q.tags.add(self.tag)

    def test_public_pages_are_available_by_named_urls(self):
        routes = [
            reverse("index"),
            reverse("hot"),
            reverse("tag", kwargs={"tag_name": self.tag.slug}),
            reverse("question", kwargs={"question_id": Question.objects.first().id}),
            reverse("login"),
            reverse("signup"),
        ]

        for url in routes:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_login_required_pages_redirect_anonymous_users(self):
        for url in [reverse("profile"), reverse("ask")]:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse("login"), response.url)

    def test_listing_pages_contain_paginator(self):
        for url in [reverse("index"), reverse("hot"), reverse("tag", kwargs={"tag_name": self.tag.slug})]:
            with self.subTest(url=url):
                response = self.client.get(url + "?page=2")
                self.assertContains(response, "pagination")

    def test_authenticated_user_without_profile_can_open_pages(self):
        user_without_profile = User.objects.create_user(username="no_profile", email="no-profile@example.com", password="StrongPass123")
        self.client.force_login(user_without_profile)

        response = self.client.get(reverse("index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "default-avatar.svg")

    def test_sidebar_context_contains_popular_tags_and_best_members(self):
        cache.clear()
        active_user = User.objects.create_user(username="active", email="active@example.com", password="StrongPass123")
        quiet_user = User.objects.create_user(username="quiet", email="quiet@example.com", password="StrongPass123")
        Profile.objects.create(user=active_user)
        Profile.objects.create(user=quiet_user)
        popular_tag = Tag.objects.create(name="popular", slug="popular")
        rare_tag = Tag.objects.create(name="rare", slug="rare")
        popular_questions = []
        for index in range(25):
            question = Question.objects.create(title=f"Popular {index}", text="Text", author=active_user)
            question.tags.add(popular_tag)
            popular_questions.append(question)
        rare_question = Question.objects.create(title="Rare", text="Text", author=quiet_user)
        rare_question.tags.add(rare_tag)
        Answer.objects.create(question=popular_questions[0], author=active_user, text="Answer 1")
        Answer.objects.create(question=popular_questions[1], author=active_user, text="Answer 2")

        context = sidebar_context()

        self.assertEqual(context["popular_tags"][0], popular_tag)
        self.assertIn(rare_tag, context["popular_tags"])
        self.assertEqual(context["best_members"][0], active_user)

    def test_sidebar_context_uses_cache_after_first_call(self):
        cache.clear()
        sidebar_context()

        with CaptureQueriesContext(connection) as captured:
            context = sidebar_context()

        self.assertEqual(len(captured), 0)
        self.assertIn("popular_tags", context)
        self.assertIn("best_members", context)


class FormsFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="author", email="author@example.com", password="StrongPass123")
        Profile.objects.create(user=self.user)
        self.question = Question.objects.create(title="Existing question", text="Text", author=self.user)

    def test_signup_creates_user_profile_and_logs_in(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "new_user",
                "email": "new@example.com",
                "nickname": "Newbie",
                "password": "VeryStrongPass123",
                "password_repeat": "VeryStrongPass123",
                "avatar": "https://example.com/avatar.png",
            },
        )
        self.assertRedirects(response, reverse("index"))
        user = User.objects.get(username="new_user")
        self.assertFalse(user.profile.avatar)

    def test_login_respects_safe_next_and_rejects_external_redirect(self):
        safe = self.client.post(
            reverse("login") + f"?next={reverse('ask')}",
            {"username": "author", "password": "StrongPass123"},
        )
        self.assertRedirects(safe, reverse("ask"))
        self.client.logout()
        unsafe = self.client.post(
            reverse("login") + "?next=https://evil.example/",
            {"username": "author", "password": "StrongPass123"},
        )
        self.assertRedirects(unsafe, reverse("index"))

    def test_logout_requires_post_and_respects_safe_next(self):
        self.client.force_login(self.user)
        get_response = self.client.get(reverse("logout") + f"?next={reverse('hot')}")
        self.assertEqual(get_response.status_code, 405)

        response = self.client.post(reverse("logout"), {"next": reverse("hot")})
        self.assertRedirects(response, reverse("hot"))

        self.client.force_login(self.user)
        unsafe = self.client.post(reverse("logout"), {"next": "https://evil.example/"})
        self.assertRedirects(unsafe, reverse("index"))

    def test_ask_form_creates_question_with_tags_and_success_overlay_message(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("ask"),
            {"title": "How to use forms?", "text": "Need help", "tags": "django, forms"},
            follow=True,
        )
        question = Question.objects.get(title="How to use forms?")
        self.assertRedirects(response, question.get_absolute_url())
        self.assertEqual(set(question.tags.values_list("name", flat=True)), {"django", "forms"})
        self.assertContains(response, "toast-container")
        self.assertContains(response, "Вопрос добавлен.")

    def test_invalid_ask_form_shows_overlay_reason(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("ask"), {"title": "", "text": "", "tags": ""})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "toast-container")
        self.assertContains(response, "Вопрос не был добавлен, потому что форма содержит ошибки.")

    def test_ask_form_invalidates_sidebar_cache_for_new_tags(self):
        self.client.force_login(self.user)
        cache.clear()
        sidebar_context()

        self.client.post(
            reverse("ask"),
            {"title": "Question with fresh tag", "text": "Need help", "tags": "fresh-tag"},
        )
        context = sidebar_context()

        self.assertIn("fresh-tag", [tag.name for tag in context["popular_tags"]])

    def test_ajax_errors_use_toast_overlay_instead_of_alert(self):
        ajax_js = Path(settings.BASE_DIR / "static" / "js" / "ajax.js").read_text(encoding="utf-8")

        self.assertIn("showAskPupkinToast", ajax_js)
        self.assertNotIn("alert(", ajax_js)

    def test_answer_form_creates_answer_and_redirects_to_anchor(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("question", kwargs={"question_id": self.question.id}),
            {"text": "Use a ModelForm."},
        )
        answer = Answer.objects.get(question=self.question)
        self.assertRedirects(response, f"{self.question.get_absolute_url()}?page=1#answer-{answer.id}")

    def test_profile_form_updates_user_and_profile(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("profile"),
            {
                "email": "updated@example.com",
                "username": "updated_author",
                "nickname": "Updated",
                "avatar": "https://example.com/updated.png",
            },
        )
        self.assertRedirects(response, reverse("profile"))
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.username, "updated_author")
        self.assertEqual(self.user.email, "updated@example.com")
        self.assertEqual(self.user.first_name, "Updated")
        self.assertFalse(self.user.profile.avatar)


class AvatarUploadTests(TestCase):
    image_bytes = (
        b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    )

    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()
        self.user = User.objects.create_user(username="avatar_user", email="avatar@example.com", password="StrongPass123")
        Profile.objects.create(user=self.user)

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_profile_accepts_image_upload_and_stores_unpredictable_media_path(self):
        self.client.force_login(self.user)
        upload = SimpleUploadedFile("avatar.gif", self.image_bytes, content_type="image/gif")

        response = self.client.post(
            reverse("profile"),
            {
                "email": "avatar-updated@example.com",
                "username": "avatar_user",
                "nickname": "Avatar",
                "avatar": upload,
            },
        )

        self.assertRedirects(response, reverse("profile"))
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.avatar.name.startswith("avatars/"))
        self.assertTrue(self.user.profile.avatar.name.endswith(".gif"))
        self.assertNotIn("avatar.gif", self.user.profile.avatar.name)

    def test_profile_rejects_non_image_avatar_upload(self):
        self.client.force_login(self.user)
        upload = SimpleUploadedFile("avatar.bmp", self.image_bytes, content_type="image/gif")

        response = self.client.post(
            reverse("profile"),
            {
                "email": "avatar@example.com",
                "username": "avatar_user",
                "nickname": "Avatar",
                "avatar": upload,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Разрешены только изображения")
        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.avatar)


class AjaxReactionTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username="author", email="author@example.com", password="StrongPass123")
        self.voter = User.objects.create_user(username="voter", email="voter@example.com", password="StrongPass123")
        self.other = User.objects.create_user(username="other", email="other@example.com", password="StrongPass123")
        for user in [self.author, self.voter, self.other]:
            Profile.objects.create(user=user)
        self.question = Question.objects.create(title="Question", text="Text", author=self.author)
        self.answer = Answer.objects.create(question=self.question, author=self.other, text="Answer")

    def post_json(self, url, payload, user=None):
        if user:
            self.client.force_login(user)
        return self.client.post(url, data=json.dumps(payload), content_type="application/json", HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    def test_question_like_requires_authenticated_user(self):
        response = self.post_json(reverse("question_vote"), {"id": self.question.id, "type": "like"})

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["error"], "auth_required")

    def test_question_like_changes_rating_and_rejects_duplicate_same_vote(self):
        url = reverse("question_vote")
        first = self.post_json(url, {"id": self.question.id, "type": "like"}, self.voter)
        duplicate = self.post_json(url, {"id": self.question.id, "type": "like"}, self.voter)
        switched = self.post_json(url, {"id": self.question.id, "type": "dislike"}, self.voter)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["rating"], 1)
        self.assertEqual(duplicate.status_code, 400)
        self.assertEqual(duplicate.json()["error"], "duplicate_vote")
        self.assertEqual(switched.status_code, 200)
        self.assertEqual(switched.json()["rating"], -1)
        self.assertEqual(QuestionLike.objects.get(user=self.voter, question=self.question).value, -1)

    def test_question_like_returns_json_error_for_missing_object(self):
        response = self.post_json(reverse("question_vote"), {"id": 999999, "type": "like"}, self.voter)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "not_found")

    def test_answer_dislike_changes_rating(self):
        response = self.post_json(reverse("answer_vote"), {"id": self.answer.id, "type": "dislike"}, self.voter)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["rating"], -1)
        self.assertEqual(AnswerLike.objects.get(user=self.voter, answer=self.answer).value, -1)

    def test_correct_answer_can_be_marked_only_by_question_author(self):
        forbidden = self.post_json(
            reverse("answer_correct"),
            {"question_id": self.question.id, "answer_id": self.answer.id},
            self.voter,
        )
        allowed = self.post_json(
            reverse("answer_correct"),
            {"question_id": self.question.id, "answer_id": self.answer.id},
            self.author,
        )

        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(forbidden.json()["error"], "forbidden")
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json(), {"answer_id": self.answer.id, "is_correct": True})
        self.answer.refresh_from_db()
        self.assertTrue(self.answer.is_correct)

    def test_correct_answer_returns_json_error_for_mismatched_answer(self):
        other_question = Question.objects.create(title="Other", text="Text", author=self.author)
        response = self.post_json(
            reverse("answer_correct"),
            {"question_id": other_question.id, "answer_id": self.answer.id},
            self.author,
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "not_found")


class PaginationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_paginate_defaults_invalid_page_values_to_first_page(self):
        request = self.factory.get("/?page=bad")
        page = paginate(list(range(30)), request, per_page=10)
        self.assertEqual(page.number, 1)

    def test_paginate_defaults_out_of_range_page_values_to_first_page(self):
        request = self.factory.get("/?page=999")
        page = paginate(list(range(30)), request, per_page=10)
        self.assertEqual(page.number, 1)


class FillDbCommandTests(TestCase):
    def test_fill_db_keeps_generated_profiles_on_default_avatar(self):
        call_command("fill_db", 1, verbosity=0)

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Profile.objects.count(), 1)
        self.assertFalse(Profile.objects.get().avatar)
