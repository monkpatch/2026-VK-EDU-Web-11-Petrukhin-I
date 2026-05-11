from django.test import SimpleTestCase
from django.urls import reverse

from .views import paginate


class PagesRoutingTests(SimpleTestCase):
    def test_main_pages_are_available_by_named_urls(self):
        routes = [
            reverse("index"),
            reverse("hot"),
            reverse("tag", kwargs={"tag_name": "django"}),
            reverse("question", kwargs={"question_id": 35}),
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
        for url in [reverse("index"), reverse("hot"), reverse("tag", kwargs={"tag_name": "django"})]:
            with self.subTest(url=url):
                response = self.client.get(url + "?page=2")
                self.assertContains(response, "pagination")
                self.assertContains(response, "page=1")


class PaginationTests(SimpleTestCase):
    def test_paginate_defaults_invalid_page_values_to_first_page(self):
        request = self.client.get(reverse("index") + "?page=bad").wsgi_request
        page = paginate(list(range(30)), request, per_page=10)
        self.assertEqual(page.number, 1)

    def test_paginate_defaults_out_of_range_page_values_to_first_page(self):
        request = self.client.get(reverse("index") + "?page=999").wsgi_request
        page = paginate(list(range(30)), request, per_page=10)
        self.assertEqual(page.number, 1)
