from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .models import Answer, Profile, Question, Tag
from .views import paginate


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
        self.assertEqual(user.profile.avatar, "https://example.com/avatar.png")

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

    def test_ask_form_creates_question_with_tags(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("ask"),
            {"title": "How to use forms?", "text": "Need help", "tags": "django, forms"},
        )
        question = Question.objects.get(title="How to use forms?")
        self.assertRedirects(response, question.get_absolute_url())
        self.assertEqual(set(question.tags.values_list("name", flat=True)), {"django", "forms"})

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
        self.assertEqual(self.user.profile.avatar, "https://example.com/updated.png")


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
