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
PROFILE_URL = reverse('posts:profile', kwargs={'username': USERNAME_AUTHOR})
PROFILE_FOLLOW_URL = reverse('posts:profile_follow',
                             kwargs={'username': USERNAME_USER})
PROFILE_UNFOLLOW_URL = reverse('posts:profile_unfollow',
                               kwargs={'username': USERNAME_USER})
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

    def test_http_statuses(self):
        httpstatus = (
            (INDEX_URL, HTTP_OK,
                self.guest),
            (GROUP_LIST_URL, HTTP_OK,
                self.guest),
            (PROFILE_URL, HTTP_OK,
                self.guest),
            (self.POST_DETAIL_URL, HTTP_OK,
                self.guest),
            (self.POST_EDIT_URL, HTTP_OK,
                self.author),
            (self.POST_EDIT_URL, HTTP_FOUND,
                self.guest),
            (POST_CREATE_URL, HTTP_OK,
                self.author),
            (POST_CREATE_URL, HTTP_FOUND,
                self.guest),
            (NOT_FOUNT_URL, HTTP_NOT_FOUND,
                self.guest),
            (FOLLOW_URL, HTTP_OK,
                self.another),
            (FOLLOW_URL, HTTP_FOUND,
                self.guest),
            (PROFILE_FOLLOW_URL, HTTP_FOUND,
                self.author),
            (PROFILE_UNFOLLOW_URL, HTTP_FOUND,
                self.author),
            (self.POST_COMMENT_URL, HTTP_FOUND,
                self.author),

        )
        for address, status, client in httpstatus:
            with self.subTest(address=address):
                self.assertEqual(client.get(address).status_code, status)

    def test_templates(self) -> None:
        templates = (
            (INDEX_URL, 'posts/index.html',
                self.guest),
            (GROUP_LIST_URL, 'posts/group_list.html',
                self.guest),
            (PROFILE_URL, 'posts/profile.html',
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

    def test_redirects(self):
        redirects = (
            (self.POST_EDIT_URL, reverse('users:login') + '?next='
             + self.POST_EDIT_URL,
             self.guest),
            (self.POST_EDIT_URL, self.POST_DETAIL_URL, self.another),
            (POST_CREATE_URL, reverse('users:login') + '?next='
             + POST_CREATE_URL, self.guest),
            (self.POST_COMMENT_URL, reverse('users:login') + '?next='
             + self.POST_COMMENT_URL, self.guest),
            (FOLLOW_URL, reverse('users:login') + '?next='
             + FOLLOW_URL, self.guest),
            (PROFILE_FOLLOW_URL, reverse('users:login') + '?next='
             + PROFILE_FOLLOW_URL, self.guest),
            (PROFILE_UNFOLLOW_URL, reverse('users:login') + '?next='
             + PROFILE_UNFOLLOW_URL, self.guest)
        )
        for address, redirect, client in redirects:
            with self.subTest(address=address):
                self.assertRedirects(
                    client.get(address, follow=True), redirect
                )
