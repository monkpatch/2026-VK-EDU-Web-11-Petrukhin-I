from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from django.urls import reverse

from .models import Question, Tag
from .views import paginate


class PagesRoutingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", email="tester@example.com", password="pass")
        self.tag = Tag.objects.create(name="django", slug="django")
        for i in range(1, 25):
            q = Question.objects.create(
                title=f"Question {i}",
                text="Some text",
                author=self.user,
                rating=i,
            )
            q.tags.add(self.tag)

    def test_main_pages_are_available_by_named_urls(self):
        routes = [
            reverse("index"),
            reverse("hot"),
            reverse("tag", kwargs={"tag_name": self.tag.slug}),
            reverse("question", kwargs={"question_id": Question.objects.first().id}),
            reverse("login"),
            reverse("signup"),
            reverse("profile"),
            reverse("ask"),
        ]

        for url in routes:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_listing_pages_contain_paginator(self):
        for url in [reverse("index"), reverse("hot"), reverse("tag", kwargs={"tag_name": self.tag.slug})]:
            with self.subTest(url=url):
                response = self.client.get(url + "?page=2")
                self.assertContains(response, "pagination")


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
