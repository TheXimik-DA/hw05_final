import shutil
import tempfile

from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from posts.models import Follow, Group, Post, User

POSTS_IN_SECOND_PAGES = 1
GROUP_SLUG = 'test_slug'
GROUP2_SLUG = 'test2'
GROUP3_SLUG = 'test3'
USERNAME = 'tigr'
USERNAME_AUTHOR = 'Authortest'
USERNAME_FOLLOWING = 'Follow'
INDEX_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:post_create')
PROFILE_URL = reverse('posts:profile',
                      kwargs={'username': USERNAME_AUTHOR})
GROUP_LIST_URL = reverse('posts:group_list',
                         kwargs={'slug': GROUP_SLUG})
GROUP2_LIST_URL = reverse('posts:group_list',
                          kwargs={'slug': GROUP2_SLUG})
GROUP3_LIST_URL = reverse('posts:group_list',
                          kwargs={'slug': GROUP3_SLUG})
FOLLOW_URL = reverse('posts:follow_index')
PROFILE_FOLLOW_URL = reverse('posts:profile_follow',
                             kwargs={'username': USERNAME_AUTHOR})
PROFILE_UNFOLLOW_URL = reverse('posts:profile_unfollow',
                               kwargs={'username': USERNAME_AUTHOR})
INDEX_PAGE_PAGINATE = INDEX_URL + '?page=2'
GROUP2_URL = f'{GROUP2_LIST_URL}?page=2'
PROFILE_PAGINATE = f'{PROFILE_URL}?page=2'
FOLLOW_URL_SEC = f'{FOLLOW_URL}?page=2'
POSTS_SEC_PAGE = 5

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.author = User.objects.create_user(username=USERNAME_AUTHOR)
        cls.follow_user = User.objects.create_user(username=USERNAME_FOLLOWING)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug=GROUP2_SLUG,
            description='Тестовое описание 2',
        )
        cls.group_3 = Group.objects.create(
            title='Тестовый заголовок 3',
            slug=GROUP3_SLUG,
            description='Тестовое описание 3    ',
        )
        cls.test_image = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый текстss',
            image=cls.test_image
        )
        Follow.objects.create(
            user=cls.follow_user,
            author=cls.author
        )
        cls.authorized = Client()
        cls.authorized.force_login(cls.user)
        cls.author_user = Client()
        cls.author_user.force_login(cls.author)
        cls.following_user = Client()
        cls.following_user.force_login(cls.follow_user)
        cls.POST_DETAIL_URL = reverse('posts:post_detail',
                                      kwargs={'post_id': cls.post.pk})
        cls.POST_EDIT_URL = reverse('posts:post_edit',
                                    kwargs={'post_id': cls.post.pk})

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_page_show_correct_context(self):
        """Шаблоны сформированы с правильным контекстом."""
        correct_context = (
            GROUP_LIST_URL,
            INDEX_URL,
            self.POST_DETAIL_URL,
            PROFILE_URL,
            FOLLOW_URL
        )
        for url in correct_context:
            with self.subTest(url=url):
                response = self.following_user.get(url)
                if 'page_obj' in response.context:
                    self.assertEqual(len(response.context['page_obj']), 1)
                    post = response.context['page_obj'][0]
                else:
                    post = response.context['post']
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.image, self.post.image)
                self.assertEqual(post.pk, self.post.pk)

    def test_cache_index_page(self):
        """Проверка сохранения кэша для index."""
        new_post = Post.objects.create(
            author=self.user,
            text='Проверка кэша'
        )
        response = self.authorized.get(INDEX_URL).content
        new_post.delete()
        after_delete_post = self.authorized.get(
            INDEX_URL).content
        self.assertEqual(response, after_delete_post)
        cache.clear()
        after_delete_cache = self.authorized.get(
            INDEX_URL
        ).content
        self.assertNotEqual(response, after_delete_cache)

    def test_post_is_not_in_incorrect_page(self):
        """Проверка, что запись не попала на страницу для
        которой не была предназначена."""
        response = self.author_user.get(GROUP3_LIST_URL)
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_paginator(self):
        Post.objects.all().delete()
        COUNT = settings.MAX_RECORDS + POSTS_SEC_PAGE
        Follow.objects.create(
            author=self.author,
            user=self.user,
        )
        Post.objects.bulk_create(
            Post(
                text=f'Тестовый текст{i}',
                author=self.author,
                group=self.group2,
            )
            for i in range(COUNT)
        )
        urls = {
            INDEX_URL: settings.MAX_RECORDS,
            INDEX_PAGE_PAGINATE: POSTS_SEC_PAGE,
            GROUP2_LIST_URL: settings.MAX_RECORDS,
            GROUP2_URL: POSTS_SEC_PAGE,
            FOLLOW_URL: settings.MAX_RECORDS,
            FOLLOW_URL_SEC: POSTS_SEC_PAGE,
            PROFILE_URL: settings.MAX_RECORDS,
            PROFILE_PAGINATE: POSTS_SEC_PAGE,
        }
        for url, num in urls.items():
            with self.subTest(
                url=url,
                num=num,
            ):
                self.assertEqual(
                  len(self.authorized.get(url).context['page_obj']), num,)

    def test_follow_authorized_author(self):
        """Проверка, что авторизованный пользователь может подписаться."""
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.follow_user).exists()
        )
        self.authorized.get(
            PROFILE_FOLLOW_URL
        )
        self.assertTrue(
            Follow.objects.filter(user=self.user, author=self.author).exists()
        )

    def test_unfollow_authorized_author(self):
        """Проверка, что авторизованный пользователь может отписаться."""
        Follow.objects.create(user=self.user, author=self.user)
        follow = Follow.objects.filter(user=self.user,
                                       author=self.user).count()
        self.assertEqual(follow, 1)
        self.authorized.get(
            PROFILE_UNFOLLOW_URL
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user, author=self.author
            ).exists()
        )

    def test_group_list_has_correct_context(self):
        """Группа в контексте Групп-ленты без искажения атрибутов"""
        group = self.authorized.get(
            GROUP_LIST_URL
        ).context['group']
        self.assertEqual(
            group.title,
            self.group.title,
        )
        self.assertEqual(
            group.description,
            self.group.description,
        )
        self.assertEqual(
            group.slug,
            self.group.slug,
        )
        self.assertEqual(
            group.pk,
            self.group.pk,
        )

    def test_profile_has_correct_context(self):
        """Автор в контексте Профиля"""
        response = self.author_user.get(
            PROFILE_URL
        )
        self.assertEqual(
            response.context['author'],
            self.author,
        )
