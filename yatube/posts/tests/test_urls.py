from django.contrib.auth import get_user_model

from django.test import TestCase, Client

from ..models import Post, Group, Comment
User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст',
            group=cls.group
        )

    def setUp(self):
        
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        # Создаем третий клиент
        self.author_client = Client()
        self.author_client.force_login(self.user)
        self.author_client.force_login(self.post.author)

    def test_url_available_for_everyone(self):
        """Адреса доступные всем пользователям"""
        templates_url_names = {
            '': 200,
            '/group/test/': 200,
            '/profile/HasNoName/': 200,
            '/posts/1/': 200,
            '/unexisting_page/': 404}
        for address, code in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, code)

    def test_availability_and_redirects(self):
        """Проверка доступности и перенаправления"""
        templates = (
            ('/create/', self.guest_client, 302),
            ('/posts/1/edit/', self.guest_client, 302),
            ('/create/', self.authorized_client, 200,),
            ('/posts/1/edit/', self.authorized_client, 302),
            ('/posts/1/edit/', self.author_client, 200),
        )
        for url, client, expected_code in templates:
            with self.subTest(address=url):
                response = client.get(url)
                self.assertEqual(response.status_code, expected_code)                

    def test_add_comment_guest_client_redirect(self):
        """Проверка перенаправления незарегистрированного 
        пользователя на login при попытке добавить комментарий"""
        response = self.guest_client.post('/posts/1/comment/')
        expected_url = '/auth/login/?next=/posts/1/comment/'
        self.assertRedirects(
            response,expected_url)

    def test_add_comment_authorized_client_redirect(self):
        """Проверка перенаправления зарегистрированного 
        пользователя на post_detail при добавлении комментарий"""
        response = self.authorized_client.post('/posts/1/comment/')
        expected_url = '/posts/1/'
        self.assertRedirects(
            response,expected_url)
