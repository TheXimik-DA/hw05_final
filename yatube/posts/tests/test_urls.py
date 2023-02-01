from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='User')
        cls.user_author = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовая запись для тестов',
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.author = Client()
        cls.authorized_client.force_login(cls.user)
        cls.author.force_login(cls.user_author)
        cls.urls = {
            '/': '/',
            'group': '/group/Slug/',
            'profile': '/profile/Author/',
            'posts': '/posts/1/',
            'post edit': '/posts/1/edit/',
            'post create': '/create/',
            'not found': '/unexisting_page/'
        }

    def test_http_statuses(self) -> None:
        httpstatus = (
            (self.urls.get('/'), HTTPStatus.OK.value,
                self.guest_client),
            (self.urls.get('group'), HTTPStatus.OK.value,
                self.guest_client),
            (self.urls.get('profile'), HTTPStatus.OK.value,
                self.guest_client),
            (self.urls.get('posts'), HTTPStatus.OK.value,
                self.guest_client),
            (self.urls.get('post edit'), HTTPStatus.OK.value,
                self.author),
            (self.urls.get('post edit'), HTTPStatus.FOUND.value,
                self.guest_client),
            (self.urls.get('post create'), HTTPStatus.OK.value,
                self.author),
            (self.urls.get('post create'), HTTPStatus.FOUND.value,
                self.guest_client),
            (self.urls.get('not found'), HTTPStatus.NOT_FOUND.value,
                self.guest_client)
        )
        for address, status, client in httpstatus:
            with self.subTest(address=address):
                self.assertEqual(client.get(address).status_code, status)

    def test_templates(self) -> None:
        templates = (
            (self.urls.get('/'), 'posts/index.html',
                self.guest_client),
            (self.urls.get('group'), 'posts/group_list.html',
                self.guest_client),
            (self.urls.get('profile'), 'posts/profile.html',
                self.guest_client),
            (self.urls.get('posts'), 'posts/post_detail.html',
                self.guest_client),
            (self.urls.get('post edit'), 'posts/create_post.html',
                self.author),
            (self.urls.get('post create'), 'posts/create_post.html',
                self.author),
        )
        for address, template, client in templates:
            with self.subTest(address=address):
                self.assertTemplateUsed(client.get(address), template)

    def test_redirects(self) -> None:
        redirects = (
            (self.urls.get('post edit'),
                reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
                self.authorized_client),
            (self.urls.get('post edit'),
                '/auth/login/?next=%2Fposts%2F1%2Fedit%2F', self.guest_client),
            (self.urls.get(
                'post create'), '/auth/login/?next=/create/',
                self.guest_client),
        )
        for address, redirect, client in redirects:
            with self.subTest(address=address):
                self.assertRedirects(
                    client.get(address, follow=True), redirect
                )
