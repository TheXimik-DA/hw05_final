from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

NOT_FOUNT_URL = '/existing_page/'
GROUP_SLUG = 'test_slug'
USERNAME_AUTHOR = 'Author'
USERNAME_USER = 'Auth_user'
FOLLOW_URL = reverse('posts:follow_index')
INDEX_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:post_create')
GROUP_LIST_URL = reverse('posts:group_list', kwargs={'slug': GROUP_SLUG})
PROFILE_URL_ANOTHER = reverse('posts:profile', kwargs={'username': USERNAME_USER})
PROFILE_URL_AUTHOR = reverse('posts:profile', kwargs={'username': USERNAME_AUTHOR})
PROFILE_FOLLOW_URL = reverse('posts:profile_follow',
                             kwargs={'username': USERNAME_USER})
PROFILE_UNFOLLOW_URL = reverse('posts:profile_unfollow',
                               kwargs={'username': USERNAME_USER})
PROFILE_FOLLOW_URL_ANOTHER = reverse('posts:profile_follow',
                                     kwargs={'username': USERNAME_AUTHOR})
PROFILE_UNFOLLOW_URL_ANOTHER = reverse('posts:profile_unfollow',
                                       kwargs={'username': USERNAME_AUTHOR})
HTTP_OK = HTTPStatus.OK.value
HTTP_FOUND = HTTPStatus.FOUND.value
HTTP_NOT_FOUND = HTTPStatus.NOT_FOUND.value


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME_USER)
        cls.user_author = User.objects.create_user(username=USERNAME_AUTHOR)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовая запись для тестов',
        )
        cls.POST_DETAIL_URL = reverse('posts:post_detail',
                                      kwargs={'post_id': cls.post.pk})
        cls.POST_EDIT_URL = reverse('posts:post_edit',
                                    kwargs={'post_id': cls.post.pk})
        cls.POST_COMMENT_URL = reverse('posts:add_comment',
                                       kwargs={'post_id': cls.post.pk})
        cls.guest = Client()
        cls.another = Client()
        cls.author = Client()
        cls.another.force_login(cls.user)
        cls.author.force_login(cls.user_author)
        cls.httpstatus_guest = (
            (INDEX_URL, HTTP_OK,
             cls.guest),
            (GROUP_LIST_URL, HTTP_OK,
             cls.guest),
            (PROFILE_URL_AUTHOR, HTTP_OK,
             cls.guest),
            (cls.POST_DETAIL_URL, HTTP_OK,
             cls.guest),
            (cls.POST_EDIT_URL, HTTP_FOUND,
             cls.guest),
            (POST_CREATE_URL, HTTP_FOUND,
             cls.guest),
            (NOT_FOUNT_URL, HTTP_NOT_FOUND,
             cls.guest),
            (FOLLOW_URL, HTTP_FOUND,
             cls.guest),
            (PROFILE_FOLLOW_URL, HTTP_FOUND,
             cls.guest),
            (PROFILE_UNFOLLOW_URL, HTTP_FOUND,
             cls.guest),
        )
        cls.httpstatus_author = (
            (cls.POST_EDIT_URL, HTTP_OK,
             cls.author),
            (POST_CREATE_URL, HTTP_OK,
             cls.author),
            (PROFILE_FOLLOW_URL, HTTP_FOUND,
             cls.author),
            (PROFILE_UNFOLLOW_URL, HTTP_FOUND,
             cls.author),
            (cls.POST_COMMENT_URL, HTTP_FOUND,
             cls.author),
        )
        cls.httpstatus_another = (
            (FOLLOW_URL, HTTP_OK,
             cls.another),
            (PROFILE_FOLLOW_URL, HTTP_FOUND,
             cls.another),
            (PROFILE_UNFOLLOW_URL, HTTP_NOT_FOUND,
             cls.another),
        )
        cls.redirects_guest = (
            (cls.POST_EDIT_URL, reverse('users:login') + '?next='
             + cls.POST_EDIT_URL,
             cls.guest),
            (POST_CREATE_URL, reverse('users:login') + '?next='
             + POST_CREATE_URL, cls.guest),
            (cls.POST_COMMENT_URL, reverse('users:login') + '?next='
             + cls.POST_COMMENT_URL, cls.guest),
            (FOLLOW_URL, reverse('users:login') + '?next='
             + FOLLOW_URL, cls.guest),
            (PROFILE_FOLLOW_URL, reverse('users:login') + '?next='
             + PROFILE_FOLLOW_URL, cls.guest),
            (PROFILE_UNFOLLOW_URL, reverse('users:login') + '?next='
             + PROFILE_UNFOLLOW_URL, cls.guest)
        )
        cls.redirects_author = (
            (cls.POST_COMMENT_URL, cls.POST_DETAIL_URL, cls.author),
            (PROFILE_FOLLOW_URL, PROFILE_URL_ANOTHER, cls.author),
            (PROFILE_UNFOLLOW_URL, PROFILE_URL_ANOTHER, cls.author),
        )
        cls.redirects_another = (
            (cls.POST_COMMENT_URL, cls.POST_DETAIL_URL, cls.another),
            (PROFILE_FOLLOW_URL_ANOTHER, PROFILE_URL_AUTHOR, cls.another),
            (PROFILE_UNFOLLOW_URL_ANOTHER, PROFILE_URL_AUTHOR, cls.another)
        )

    def test_http_statuses_guest(self):
        for address, status, client in self.httpstatus_guest:
            with self.subTest(address=address):
                self.assertEqual(client.get(address).status_code, status)

    def test_http_statuses_author(self):
        for address, status, client in self.httpstatus_author:
            with self.subTest(address=address):
                self.assertEqual(client.get(address).status_code, status)

    def test_http_statuses_another(self):
        for address, status, client in self.httpstatus_another:
            with self.subTest(address=address):
                self.assertEqual(client.get(address).status_code, status)

    def test_templates(self) -> None:
        templates = (
            (INDEX_URL, 'posts/index.html',
                self.guest),
            (GROUP_LIST_URL, 'posts/group_list.html',
                self.guest),
            (PROFILE_URL_AUTHOR, 'posts/profile.html',
                self.guest),
            (self.POST_DETAIL_URL, 'posts/post_detail.html',
                self.guest),
            (self.POST_EDIT_URL, 'posts/create_post.html',
                self.author),
            (POST_CREATE_URL, 'posts/create_post.html',
                self.author),
            (NOT_FOUNT_URL, 'core/404.html',
                self.author),
            (FOLLOW_URL, 'posts/follow.html',
                self.author),
        )
        for address, template, client in templates:
            with self.subTest(address=address):
                self.assertTemplateUsed(client.get(address), template)

    def test_redirects_guest(self):
        for address, redirect, client in self.redirects_guest:
            with self.subTest(address=address):
                self.assertRedirects(
                    client.get(address, follow=True), redirect)

    def test_redirects_author(self):
        for address, redirect, client in self.redirects_author:
            with self.subTest(address=address):
                self.assertRedirects(
                    client.get(address, follow=True), redirect)

    def test_redirects_another(self):
        for address, redirect, client in self.redirects_another:
            with self.subTest(address=address):
                self.assertRedirects(
                    client.get(address, follow=True), redirect)
