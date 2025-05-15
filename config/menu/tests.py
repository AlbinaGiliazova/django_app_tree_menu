from django.test import TestCase, RequestFactory
from django.urls import path, reverse, clear_url_caches
from django.template import Template, Context
from django.conf import settings
from django.http import HttpResponse
from django.test.utils import CaptureQueriesContext
from django.db import connection

# Импорт ваших моделей и тегов
from menu.models import Menu, MenuItem

# Нужна небольшая «заглушка» в URLConf, чтобы тестировать named_url
def dummy_view(request):
    return HttpResponse("dummy")

urlpatterns = [
    path("foo/bar/", dummy_view, name="foo-bar"),
]

class TreeMenuTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Подключаем наши тестовые урлы
        settings.ROOT_URLCONF, cls._old_root = __name__, settings.ROOT_URLCONF
        clear_url_caches()

    @classmethod
    def tearDownClass(cls):
        settings.ROOT_URLCONF = cls._old_root
        clear_url_caches()
        super().tearDownClass()

    def setUp(self):
        # Фабрика запросов для шаблонного тэга
        self.factory = RequestFactory()

        # Создаём два меню, проверим, что draw_menu берёт только нужное
        self.menu1 = Menu.objects.create(name="main")
        self.menu2 = Menu.objects.create(name="secondary")

        # Структура меню main:
        # Home (/), About (/about/), Services (/services/)
        # Services → Web (named_url "foo-bar"), Mobile (/services/mobile/)
        self.home = MenuItem.objects.create(
            menu=self.menu1, title="Home", url="/", order=0
        )
        self.about = MenuItem.objects.create(
            menu=self.menu1, title="About", url="/about/", order=1
        )
        self.services = MenuItem.objects.create(
            menu=self.menu1, title="Services", url="/services/", order=2
        )
        self.web = MenuItem.objects.create(
            menu=self.menu1, parent=self.services,
            title="Web", named_url="foo-bar", order=0
        )
        self.mobile = MenuItem.objects.create(
            menu=self.menu1, parent=self.services,
            title="Mobile", url="/services/mobile/", order=1
        )

        # В меню secondary один пункт
        self.sec = MenuItem.objects.create(
            menu=self.menu2, title="Only", url="/only/", order=0
        )

    def render_menu(self, menu_name, path):
        """
        Рендерит {% draw_menu %} для заданного menu_name
        и симулированного текущего URL path.
        Возвращает tuple (rendered_html, SQL_count).
        """
        request = self.factory.get(path)
        tmpl = Template("{% load menu_tags %}{% draw_menu '" + menu_name + "' %}")
        ctx = Context({'request': request})
        # Засекаем число запросов
        with CaptureQueriesContext(connection) as ctx_manager:
            html = tmpl.render(ctx)
        return html, len(ctx_manager)

    def test_single_query_per_menu(self):
        html, sql_count = self.render_menu("main", "/")
        self.assertEqual(sql_count, 1, "Должен быть ровно 1 SQL-запрос при рендере меню")

    def test_only_relevant_menu_items(self):
        html, _ = self.render_menu("secondary", "/")
        self.assertIn("Only", html)
        self.assertNotIn("Home", html)

    def test_active_and_expanded_branches(self):
        # Путь /foo/bar/ → должен подсветиться пункт Web
        html, _ = self.render_menu("main", "/foo/bar/")
        # Web — активный
        self.assertIn('class="active', html)
        self.assertIn("Web", html)
        # Родитель Services должен быть раскрыт (появится подсписок)
        self.assertIn("Services", html)
        self.assertIn("<ul", html.split("Services")[1])  # после Services идёт подсписок

    def test_first_level_under_active_expanded(self):
        # Если кликаем на Services, раскрываются Web и Mobile
        html, _ = self.render_menu("main", "/services/")
        self.assertIn("Services", html)
        # И оба дочерних
        self.assertIn("Web", html)
        self.assertIn("Mobile", html)

    def test_named_url_resolution(self):
        # Для named_url должно правильно подставляться href через {% url %}
        html, _ = self.render_menu("main", "/foo/bar/")
        url = reverse("foo-bar")
        self.assertIn(f'href="{url}"', html)

    def test_ordering_of_items(self):
        # Меню рисуется в порядке order=0,1,2
        html, _ = self.render_menu("main", "/")
        idx_home = html.index("Home")
        idx_about = html.index("About")
        idx_services = html.index("Services")
        self.assertTrue(idx_home < idx_about < idx_services)
