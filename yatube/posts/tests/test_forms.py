import shutil
import tempfile
from http import HTTPStatus

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from posts.models import Group, Post, User, Comment

GROUP_SLUG = 'slug'
USERNAME_AUTHOR = 'Author'
USERNAME_USER = 'Auth_user'
INDEX_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:post_create')
GROUP_LIST_URL = reverse('posts:group_list', kwargs={'slug': GROUP_SLUG})
PROFILE_URL = reverse('posts:profile', kwargs={'username': USERNAME_AUTHOR})

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=USERNAME_AUTHOR)
        cls.auth_user = User.objects.create_user(username=USERNAME_USER)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.new_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст поста',
            group=cls.group,
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.test_image = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.POST_DETAIL_URL = reverse('posts:post_detail',
                                      kwargs={'post_id': cls.post.pk})
        cls.POST_EDIT_URL = reverse('posts:post_edit',
                                    kwargs={'post_id': cls.post.pk})
        cls.COMMENT_ADD = reverse('posts:add_comment',
                                  kwargs={'post_id': cls.post.pk})
        cls.guest_client = Client()
        cls.authorized_client_author = Client()
        cls.authorized_client_author.force_login(cls.author)
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.auth_user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Создание поста."""
        post_set = set(
            Post.objects.all()
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.pk,
            'image': self.test_image
        }
        response = self.authorized_client_author.post(
            POST_CREATE_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, PROFILE_URL
        )
        post_new_set = set(
            Post.objects.all()
        )
        difference_sets_of_posts = post_new_set.difference(
            post_set
        )
        self.assertEqual(
            len(difference_sets_of_posts), 1
        )
        post = difference_sets_of_posts.pop()
        self.assertEqual(
            post.text, form_data['text']
        )
        self.assertEqual(
            post.group.pk, form_data['group']
        )
        self.assertEqual(
            post.author, self.author
        )
        self.assertEqual(
            post.image, Post.objects.get(pk=2).image
        )

    def test_author_edit_post(self):
        """Редактирование поста."""
        form_data = {
            'text': 'Измененный текст',
            'group': self.new_group.pk,
        }
        response = self.authorized_client_author.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        post_edit = Post.objects.get(
            id=self.post.pk
        )
        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertEqual(
            post_edit.text, form_data['text']
        )
        self.assertEqual(
            post_edit.group.pk, form_data['group']
        )
        self.assertRedirects(
            response, self.POST_DETAIL_URL
        )
        self.assertEqual(
            post_edit.author, self.author
        )

    def test_guest_client_not_create_form(self):
        """Проверяем, что анонимный пользователь не создает запись в Post
        и перенаправляется на страницу /auth/login/ """
        count_post = Post.objects.count()
        form_data = {
            'text': 'Test text'
        }
        response = self.guest_client.post(
            POST_CREATE_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('users:login') + '?next='
            + POST_CREATE_URL)
        self.assertEqual(count_post, 1)

    def test_authorized_not_edit_form(self):
        """ Проверяем, что зарегистрированный пользователь
        не может редактировать чужую запись."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        test_image = SimpleUploadedFile(
            name='small1.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Test edit text',
            'group': self.new_group.pk,
            'image': test_image
        }
        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)
        self.assertNotEqual(self.post.text, form_data['text'])
        self.assertNotEqual(self.post.group, form_data['group'])
        self.assertNotEqual(self.post.image, form_data['image'])

    def test_guest_client_not_edit_post(self):
        """Проверяем, что неавторизованный пользователь
        не может редактировать записи"""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        test_image = SimpleUploadedFile(
            name='small1.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Test edit text',
            'group': self.new_group.pk,
            'image': test_image
        }
        response = self.guest_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('users:login') + '?next='
            + self.POST_EDIT_URL
        )
        self.assertNotEqual(self.post.text, form_data['text'])
        self.assertNotEqual(self.post.group, form_data['group'])
        self.assertNotEqual(self.post.image, form_data['image'])

    def test_authorized_client_comments_post(self):
        """Проверяем, что авторизованный пользователь
        может комментировать записи"""
        form_data = {
            'text': 'Text comment'
        }
        response = self.authorized_client.post(
            self.COMMENT_ADD,
            data=form_data,
            follow=True
        )
        comment = Comment.objects.get(pk=1)
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.auth_user)
        self.assertEqual(comment.post, self.post)
        self.assertRedirects(response, self.POST_DETAIL_URL)

    def test_guest_client_not_comment_post(self):
        """Проверяем, что незарегистрированный пользователь
        не может комментировать записи"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Comment guest'
        }
        response = self.guest_client.post(
            self.COMMENT_ADD,
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertRedirects(
            response,
            reverse('users:login') + '?next='
            + self.COMMENT_ADD
        )
