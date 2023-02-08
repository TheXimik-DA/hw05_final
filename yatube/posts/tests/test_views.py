from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from django.conf import settings

from posts.models import Follow, Group, Post, User

GROUP_SLUG = 'test_slug'
GROUP2_SLUG = 'test2'
USERNAME = 'tigr'
USERNAME_AUTHOR = 'Authortest'
INDEX_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:post_create')
GROUP_LIST_URL = reverse('posts:group_list',
                         kwargs={'slug': GROUP_SLUG})
GROUP2_LIST_URL = reverse('posts:group_list',
                          kwargs={'slug': GROUP2_SLUG})
FOLLOW_URL = reverse('posts:follow_index')
PROFILE_FOLLOW_URL = reverse('posts:profile_follow',
                             kwargs={'username': USERNAME_AUTHOR})
PROFILE_UNFOLLOW_URL = reverse('posts:profile_unfollow',
                               kwargs={'username': USERNAME_AUTHOR})


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.author = User.objects.create_user(username=USERNAME_AUTHOR)
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
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый текстss',
            pub_date='25.02.1995',
        )
        Follow.objects.create(
            user=cls.user,
            author=cls.author
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.author_user = Client()
        cls.author_user.force_login(cls.author)
        cls.POST_DETAIL_URL = reverse('posts:post_detail',
                                      kwargs={'post_id': cls.post.pk})
        cls.POST_EDIT_URL = reverse('posts:post_edit',
                                    kwargs={'post_id': cls.post.pk})
        cls.PROFILE_URL = reverse('posts:profile',
                                  kwargs={'username': cls.author.username})

    def test_page_show_correct_context(self):
        """Шаблоны сформированы с правильным контекстом."""
        correct_context = (
            GROUP_LIST_URL,
            INDEX_URL,
            self.POST_DETAIL_URL,
            self.PROFILE_URL,
            FOLLOW_URL
        )
        for url in correct_context:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                if 'page_obj' in response.context:
                    post = response.context['page_obj'][0]
                else:
                    post = response.context['post']
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.group, self.post.group)
                self.assertEqual(post.text, self.post.text)

    def test_cache_index_page(self):
        """Проверка сохранения кэша для index."""
        new_post = Post.objects.create(
            author=self.user,
            text='Проверка кэша'
        )
        response = self.authorized_client.get(INDEX_URL).content
        new_post.delete()
        after_delete_post = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertEqual(response, after_delete_post)
        cache.clear()
        after_delete_cache = self.authorized_client.get(
            reverse('posts:index')
        ).content
        self.assertNotEqual(response, after_delete_cache)

    def test_post_is_not_in_incorrect_group(self):
        """Проверка, что запись не попала на страницу сообщества,
        для которой не была предназначена."""
        urls = (
            GROUP2_LIST_URL,
            FOLLOW_URL
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertNotContains(response, Post)

    def test_paginator(self):
        cache.clear()
        Post.objects.bulk_create(
            Post(
                author=self.author,
                text=f'{i + 1} test',
                group=self.group
            )
            for i in range(1, settings.MAX_RECORDS)
        )
        for url in [
            INDEX_URL,
            GROUP_LIST_URL,
            self.PROFILE_URL,
        ]:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']), settings.MAX_RECORDS
                )
                response_second = self.authorized_client.get(
                    f'{url}?page=2'
                )
                self.assertEqual(
                    len(response_second.context['page_obj']),
                    settings.MAX_RECORDS
                )

    def test_follow_authorized_author(self):
        """Проверка, что авторизованный пользователь может подписаться."""
        cache.clear()
        self.authorized_client.get(PROFILE_FOLLOW_URL)
        self.assertTrue(
            Follow.objects.filter(user=self.user, author=self.author).exists()
        )

    def test_unfollow_authorized_author(self):
        """Проверка, что авторизованный пользователь может отписаться."""
        self.authorized_client.get(PROFILE_UNFOLLOW_URL)
        self.assertEqual(Follow.objects.count(), 0)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user, author=self.author
            ).exists()
        )
