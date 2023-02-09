from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

NOT_FOUND_URL = '/existing_page/'
GROUP_SLUG = 'test_slug'
USERNAME_AUTHOR = 'Author'
USERNAME_USER = 'Auth_user'
LOGIN = reverse('users:login')
FOLLOW_URL = reverse('posts:follow_index')
INDEX_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:post_create')
GROUP_LIST_URL = reverse('posts:group_list', kwargs={'slug': GROUP_SLUG})
PROFILE_URL_ANOTHER = reverse(
    'posts:profile',
    kwargs={'username': USERNAME_USER}
)
PROFILE_URL_AUTHOR = reverse(
    'posts:profile',
    kwargs={'username': USERNAME_AUTHOR}
)
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
        cls.GUEST_POST_EDIT = f'{LOGIN}?next={cls.POST_EDIT_URL}'
        cls.GUEST_CREATE_POST = f'{LOGIN}?next={POST_CREATE_URL}'
        cls.GUEST_POST_COMMENT = f'{LOGIN}?next={cls.POST_COMMENT_URL}'
        cls.GUEST_FOLLOW = f'{LOGIN}?next={FOLLOW_URL}'
        cls.GUEST_PROFILE_FOLLOW = f'{LOGIN}?next={PROFILE_FOLLOW_URL}'
        cls.GUEST_PROFILE_UNFOLLOW = f'{LOGIN}?next={PROFILE_UNFOLLOW_URL}'
        cls.guest = Client()
        cls.another = Client()
        cls.author = Client()
        cls.another.force_login(cls.user)
        cls.author.force_login(cls.user_author)

    def test_http_statuses(self):
        http_status = (
            (INDEX_URL, HTTP_OK,
             self.guest),
            (GROUP_LIST_URL, HTTP_OK,
             self.guest),
            (PROFILE_URL_AUTHOR, HTTP_OK,
             self.guest),
            (self.POST_DETAIL_URL, HTTP_OK,
             self.guest),
            (self.POST_EDIT_URL, HTTP_FOUND,
             self.guest),
            (POST_CREATE_URL, HTTP_FOUND,
             self.guest),
            (NOT_FOUND_URL, HTTP_NOT_FOUND,
             self.guest),
            (FOLLOW_URL, HTTP_FOUND,
             self.guest),
            (PROFILE_FOLLOW_URL, HTTP_FOUND,
             self.guest),
            (PROFILE_UNFOLLOW_URL, HTTP_FOUND,
             self.guest),
            (self.POST_EDIT_URL, HTTP_OK,
             self.author),
            (POST_CREATE_URL, HTTP_OK,
             self.author),
            (PROFILE_FOLLOW_URL, HTTP_FOUND,
             self.author),
            (PROFILE_UNFOLLOW_URL, HTTP_FOUND,
             self.author),
            (self.POST_COMMENT_URL, HTTP_FOUND,
             self.author),
            (FOLLOW_URL, HTTP_OK,
             self.another),
            (PROFILE_FOLLOW_URL, HTTP_FOUND,
             self.another),
            (PROFILE_UNFOLLOW_URL, HTTP_FOUND,
             self.another),
        )
        for address, status, client in http_status:
            with self.subTest(address=address, client=client):
                response = client.get(address)
                self.assertEqual(response.status_code, status)

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
            (NOT_FOUND_URL, 'core/404.html',
                self.author),
            (FOLLOW_URL, 'posts/follow.html',
                self.author),
        )
        for address, template, client in templates:
            with self.subTest(address=address, client=client):
                self.assertTemplateUsed(client.get(address), template)

    def test_redirects(self):
        urls_redirects = (
            (self.POST_EDIT_URL, self.GUEST_POST_EDIT,
             self.guest),
            (POST_CREATE_URL, self.GUEST_CREATE_POST, self.guest),
            (self.POST_COMMENT_URL, self.GUEST_POST_COMMENT, self.guest),
            (FOLLOW_URL, self.GUEST_FOLLOW, self.guest),
            (PROFILE_FOLLOW_URL, self.GUEST_PROFILE_FOLLOW, self.guest),
            (PROFILE_UNFOLLOW_URL, self.GUEST_PROFILE_UNFOLLOW, self.guest),
            (self.POST_COMMENT_URL, self.POST_DETAIL_URL, self.author),
            (PROFILE_FOLLOW_URL, PROFILE_URL_ANOTHER, self.author),
            (PROFILE_UNFOLLOW_URL, PROFILE_URL_ANOTHER, self.author),
            (self.POST_COMMENT_URL, self.POST_DETAIL_URL, self.another),
            (PROFILE_FOLLOW_URL_ANOTHER, PROFILE_URL_AUTHOR, self.another),
            (PROFILE_UNFOLLOW_URL_ANOTHER, PROFILE_URL_AUTHOR, self.another),
        )
        for address, redirect, client in urls_redirects:
            with self.subTest(address=address, client=client):
                self.assertRedirects(
                    client.get(address, follow=True), redirect)
