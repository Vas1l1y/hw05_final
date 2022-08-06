import shutil
import tempfile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from posts.models import Post, Group
from django.core.cache import cache
User = get_user_model()

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test-slug',
            description='Тестовое описание')
        small_gif = (            
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст',
            image=uploaded,
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        # Создаем неавторизованный клиент
        cache.clear()
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        self.author = self.authorized_client.force_login(self.post.author)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'HasNoName'}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': 1}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            '/crash/': 'core/404.html'}
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_urls_post_edit_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        self.authorized_client.force_login(self.post.author)
        templates_pages_names = {
            reverse('posts:post_edit',
                    kwargs={'post_id': 1}): 'posts/create_post.html'}
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_index_show_correct_context(self):
        """Шаблон index  сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_image = first_object.image
        # Проверяем текст поста
        self.assertEqual(post_text_0, 'Текст')
        # Проверяет картинку
        self.assertEqual(post_image, 'posts/small.gif')

    def test_group_list_show_correct_context(self):
        """Шаблон group_list  сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        self.assertEqual(
            response.context.get('group').title, 'Заголовок')
        self.assertEqual(
            response.context.get('group').description, 'Тестовое описание')
        self.assertEqual(
            response.context.get('group').slug, 'test-slug')
        first_object = response.context['page_obj'][0]
        post_image = first_object.image
        self.assertEqual(post_image, 'posts/small.gif')

    def test_profile_show_correct_context(self):
        """Шаблон profile  сформирован с правильным контекстом."""
        # self.authorized_client.force_login(self.post.author)
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'HasNoName'}))
        post_detail_obj = response.context['author'].username
        self.assertEqual(post_detail_obj, 'HasNoName')
        # # Проверяет картинку
        first_object = self.post.image
        self.assertEqual(first_object, 'posts/small.gif')
        # first_object = self.post.image
        # self.assertIn(first_object, 'posts/small.gif')

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail  сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': 1}))
        post_detail_obj = response.context['posts'].pk
        self.assertEqual(post_detail_obj, 1)
        post_image = response.context['posts'].image
        self.assertEqual(post_image, 'posts/small.gif')

    # Проверка словаря контекста создания поста (в нём передаётся форма)
    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    # Проверка словаря контекста создания поста (в нём передаётся форма)
    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        self.authorized_client.force_login(self.post.author)
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': 1}))
        # post_edit = response.context['posts'].pk
        # self.assertEqual(post_edit, 1)
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth1')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test-slug1',
            description='Тестовое описание'
        )
        for i in range(13):
            cls.post = Post.objects.create(
                text=str(i) + '. Текст 1',
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        cache.clear()
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username='Vasya')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records_index(self):
        """Проверяем паджинатор первой страницы index
        Проверка: количество постов на первой странице равно 10"""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records_index(self):
        """Проверяем паджинатор второй страницы index
        Проверка: на второй странице должно быть 3 поста"""
        response = self.client.get('', {'page': 2})
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_contains_ten_records_group_list(self):
        """Проверяем паджинатор первой страницы group_list
        Проверка: количество постов на первой странице равно 10"""
        response = self.client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug1'}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records_group_list(self):
        """Проверяем паджинатор второй страницы group_list
        Проверка: на второй странице должно быть 3 поста"""
        response = self.client.get(reverse('posts:group_list',
                                   kwargs={'slug': 'test-slug1'})
                                   + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_page_contains_ten_records_profile(self):
        """Проверяем паджинатор страницы profile
        Проверка: количество постов на первой странице равно 10"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'auth1'}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records_profile(self):
        """Проверяем паджинатор второй страницы profile
        Проверка: на второй странице должно быть 3 поста"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'auth1'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)


class PostViewsTest_create_post_in(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test-slug2',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Это текст должен быть в тестах',
            group=cls.group,
        )

    def setUp(self):
        cache.clear()
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username='Vasya')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_create_post_in_group_list(self):
        """Проверяем, что созаднный пост, есть на group_list"""
        response = self.authorized_client.get(reverse('posts:group_list',
                                              kwargs={'slug': 'test-slug2'}))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context['page_obj'][0]
        self.assertEqual(self.post, first_object)

    def test_create_post_in_index(self):
        """Проверяем, что созаднный пост, есть на index"""
        response = self.authorized_client.get(reverse('posts:index'))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context['page_obj'][0]
        self.assertEqual(self.post, first_object)

    def test_create_post_in_profile(self):
        """Проверяем, что созаднный пост, есть на profile"""
        self.authorized_client.force_login(self.post.author)
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username': 'auth2'}))
        post_detail_obj = response.context['page_obj'][0]
        self.assertEqual(self.post, post_detail_obj)


class PostViewsTest_create_post_not_in_group(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth3')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test-slug2',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Заголовок',
            slug='test-slug3',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Это текст должен быть в тестах',
            group=cls.group,
        )
        cls.post_54 = Post.objects.create(
            author=cls.user,
            text='Может этот',
            group=cls.group_2,
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        cache.clear()
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username='Vasyan')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_create_post_not_in_group_list(self):
        """Проверяем, что созаднный пост, отсутствует в группе"""
        response = self.authorized_client.get(reverse('posts:group_list',
                                              kwargs={'slug': 'test-slug3'}))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context['page_obj'][0]
        self.assertNotEqual(self.post, first_object)


class PostsIndexCache(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестирование кэша главной страницы',
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
        self.user = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_cache_for_index(self):
        """Тест проверяющий работу кэширования страницы"""
        response_first = self.authorized_client.get(
            reverse('posts:index'))
        Post.objects.create(
            text='Тестирование кэша главной страницы',
            author=self.user,
        )
        response_two = self.authorized_client.get(
            reverse('posts:index'))
        self.assertEqual(response_first.content, response_two.content)
        cache.clear()
        response_three = self.authorized_client.get(
            reverse('posts:index'))
        self.assertNotEqual(response_first.content, response_three.content)


class PostsFollowAuthor(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_masha = User.objects.create_user(username='Masha')
        cls.user_vasya = User.objects.create_user(username='Vasya')
        cls.post_masha = Post.objects.create(
            author=cls.user_masha,
            text='Ученье — свет, а неученье — тьма',
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        # Создаем неавторизованный клиент
        # self.guest_client = Client()
        # Создаем пользователя
        # self.user = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        self.authorized_masha = Client()
        self.authorized_vasya = Client()
        # Авторизуем пользователя
        self.authorized_masha.force_login(self.user_masha)
        self.authorized_vasya.force_login(self.user_vasya)

    def test_no_see_post_in_follow_index_unfollowed_user(self):
        """Новая запись пользователя не появляется в follow index тех,
        кто на него не подписан"""
        # Проверяем, что созданный пост доступен на главной странице
        response_index = self.authorized_vasya.get(reverse('posts:index'))
        # Взяли первый элемент из списка главной страницы
        first_object_index = response_index.context['page_obj'][0]
        # получили текст поста автора
        post_text_index = first_object_index.text
        # Сравниваем полученный текст с созданным постом
        self.assertEqual(post_text_index, 'Ученье — свет, а неученье — тьма')
        # Взяли +первый элемент из списка страницы follow index
        response_follow_index = self.authorized_vasya.get(
            reverse('posts:follow_index'))
        self.assertNotEqual(
            response_index.content,
            response_follow_index.content)

    def test_see_post_in_follow_index_followed_user(self):
        """Новая запись пользователя появляется в follow index тех,
        кто на него подписан"""
        # Получаем пустую follow index для юзера
        response_follow_index_none_post = self.authorized_vasya.get(
            reverse('posts:follow_index'))
        # Добавляем пользователя "Маша" в избранное/подписываемся
        self.authorized_vasya.get('/profile/Masha/follow/')
        # Проверяем, что созданный пост доступен на главной странице
        response_index = self.authorized_vasya.get(reverse('posts:index'))
        # Взяли первый элемент из списка главной страницы
        first_object_index = response_index.context['page_obj'][0]
        # Получаем текст поста
        post_text_index = first_object_index.text
        # Сравниваем полученный текст с созданным постом
        self.assertEqual(post_text_index, 'Ученье — свет, а неученье — тьма')
        response_follow_index = self.authorized_vasya.get(
            reverse('posts:follow_index'))
        # Взяли первый элемент из списка страницы follow index
        first_object_f_index = response_follow_index.context['page_obj'][0]
        # Получаем текст поста
        post_text_follow_index = first_object_f_index.text
        # Сравниваем полученный текст с созданным постом
        self.assertEqual(
            post_text_follow_index,
            'Ученье — свет, а неученье — тьма')
        # Проверяем, что содержимое страниц одинаковое
        self.assertEqual(first_object_index, first_object_f_index)
        # Отписываемся от автора
        self.authorized_vasya.get('/profile/Masha/unfollow/')
        # Получаем follow index для юзера после отписки
        response_follow_index_unfollow = self.authorized_vasya.get(
            reverse('posts:follow_index'))
        # сравниваем follow до подписки на автора и после отписки
        self.assertEqual(
            response_follow_index_none_post.content,
            response_follow_index_unfollow.content)
