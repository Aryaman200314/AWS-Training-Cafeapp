"""Application behavior checks using Python's built-in unittest runner."""

from html.parser import HTMLParser
import os
import unittest
from unittest.mock import patch

from app import app
from menu import get_menu


class PageParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.cards = []
        self.buttons = []
        self.resources = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "article" and "data-category" in attrs:
            self.cards.append(attrs["data-category"])
        if tag == "button" and "data-filter" in attrs:
            self.buttons.append(attrs)
        if tag == "script" and "src" in attrs:
            self.resources.append(attrs["src"])
        if tag == "link" and attrs.get("rel") in ("stylesheet", "icon"):
            self.resources.append(attrs["href"])


class CloudCafeTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.client = app.test_client()

    def test_homepage_contains_exactly_eight_complete_menu_items(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Cloud Café", html)
        page = PageParser(html)
        self.assertCountEqual(page.cards, ["Coffee"] * 3 + ["Tea"] * 2 + ["Snacks"] * 3)
        for item in get_menu():
            with self.subTest(item=item["name"]):
                self.assertIn(item["name"], html)
                self.assertIn(item["description"], html)
                self.assertIn(f"${item['price']:.2f}", html)

    def test_defaults_display_hostname_and_version(self):
        with patch("app.socket.gethostname", return_value="training-host"):
            html = self.client.get("/").get_data(as_text=True)
        self.assertIn('id="server-name">training-host<', html)
        self.assertIn('id="app-version">1.0<', html)

    def test_environment_overrides_and_arbitrary_alb_host(self):
        with patch.dict(os.environ, {"SERVER_NAME": "Alain-demo", "APP_VERSION": "2.7"}):
            response = self.client.get("/", headers={"Host": "10.0.1.23:8080"})
        self.assertEqual(response.status_code, 200)
        self.assertIn('id="server-name">Alain-demo<', response.text)
        self.assertIn('id="app-version">2.7<', response.text)
        self.assertIsNone(app.config["SERVER_NAME"])

    def test_empty_environment_values_use_defaults(self):
        with patch.dict(os.environ, {"SERVER_NAME": "", "APP_VERSION": ""}):
            with patch("app.socket.gethostname", return_value="fallback-host"):
                html = self.client.get("/").text
        self.assertIn('id="server-name">fallback-host<', html)
        self.assertIn('id="app-version">1.0<', html)

    def test_environment_values_are_html_escaped(self):
        with patch.dict(os.environ, {"SERVER_NAME": "<script>alert(1)</script>", "APP_VERSION": "<b>2</b>"}):
            html = self.client.get("/").text
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&lt;b&gt;2&lt;/b&gt;", html)
        self.assertNotIn("<script>alert(1)</script>", html)

    def test_homepage_cannot_be_cached(self):
        response = self.client.get("/")
        self.assertTrue(response.cache_control.no_store)
        self.assertTrue(response.cache_control.no_cache)
        self.assertEqual(response.headers["Pragma"], "no-cache")
        self.assertEqual(response.headers["Expires"], "0")

    def test_health_is_exact_plain_text_and_independent_of_menu_and_templates(self):
        with patch("app.get_menu", side_effect=RuntimeError("Menu unavailable")):
            with patch("app.render_template", side_effect=RuntimeError("Template unavailable")):
                response = self.client.get("/health", headers={"Host": "10.0.0.8:8080"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"OK")
        self.assertEqual(response.mimetype, "text/plain")
        self.assertNotIn("Location", response.headers)
        self.assertNotIn("Set-Cookie", response.headers)

    def test_filter_controls_have_accessible_initial_state(self):
        page = PageParser(self.client.get("/").text)
        self.assertEqual([button["data-filter"] for button in page.buttons], ["All", "Coffee", "Tea", "Snacks"])
        self.assertEqual([button["aria-pressed"] for button in page.buttons], ["true", "false", "false", "false"])

    def test_assets_are_local_and_load(self):
        page = PageParser(self.client.get("/").text)
        self.assertEqual(len(page.resources), 3)
        for resource in page.resources:
            with self.subTest(resource=resource):
                self.assertTrue(resource.startswith("/static/"))
                response = self.client.get(resource)
                self.assertEqual(response.status_code, 200)
                response.close()

    def test_menu_calls_do_not_share_mutable_state(self):
        menu = get_menu()
        menu[0]["name"] = "Changed by caller"
        menu.pop()
        self.assertEqual(len(get_menu()), 8)
        self.assertEqual(get_menu()[0]["name"], "Cloud Nine Latte")

    def test_debug_disabled(self):
        self.assertFalse(app.debug)


if __name__ == "__main__":
    unittest.main()
