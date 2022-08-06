import shutil
import tempfile

from django.contrib.auth import get_user_model
from posts.models import Post, Group, Comment
from posts.forms import PostForm, CommentForm
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

User = get_user_model()
# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user1', password='123')
        cls.group = Group.objects.create(
            title='Называние Группы',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )
        cls.form = PostForm()
        cls.small_gif_code = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif_code,
            content_type='image/gif'
        )

        form_data = {
            'text': 'Тестовый текст 2',
            'group': self.group.id,
            'image': uploaded,
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': 'user1'}))

        self.assertEqual(Post.objects.count(), posts_count + 1)

        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст 2',
                author=self.user,
                group=self.group,
                image='posts/small.gif',
            ).exists()
        )

    def test_edit_post(self):

        uploaded = SimpleUploadedFile(
            name='small2.gif',
            content=self.small_gif_code,
            content_type='image/gif'
        )

        form_data = {
            'text': 'Тестовый текст 2 изменен',
            'group': self.group.id,
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}))
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст 2 изменен',
                author=self.user,
                group=self.group,
                image='posts/small2.gif',
            ).exists()
        )

    def test_post_comment_authorized_client(self):
        """Авторизованный пользователь может добавить комментарий"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Просто бомбезно',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Comment.objects.filter(
                text='Просто бомбезно',
            ).exists()
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)

    def test_post_comment_guest_client(self):
        """Не авторизованный пользователь не может добавить комментарий"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Просто бомбезно',
        }
        self.guest_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True
        )
        self.assertFalse(
            Comment.objects.filter(
                text='Просто бомбезно',
            ).exists()
        )
        self.assertEqual(Comment.objects.count(), comments_count)
