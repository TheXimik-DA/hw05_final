from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, Follow, User

GROUP_SLUG = 'test_slug'
USERNAME = 'tigr'
INDEX_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:post_create')
GROUP_LIST_URL = reverse('posts:group_list', kwargs={'slug': GROUP_SLUG})
PROFILE_URL = reverse('posts:profile', kwargs={'username': USERNAME})


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=GROUP_SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Тестовый текст',
            pub_date='25.02.1995',
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.POST_DETAIL_URL = reverse('posts:post_detail',
                                      kwargs={'post_id': cls.post.pk})
        cls.POST_EDIT_URL = reverse('posts:post_edit',
                                    kwargs={'post_id': cls.post.pk})

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        urls_templates_data = [
            (INDEX_URL, 'posts/index.html'),
            (GROUP_LIST_URL, 'posts/group_list.html'),
            (PROFILE_URL, 'posts/profile.html'),
            (POST_CREATE_URL, 'posts/create_post.html'),
            (self.POST_DETAIL_URL, 'posts/post_detail.html'),
            (self.POST_EDIT_URL, 'posts/create_post.html')
        ]
        for url, template in urls_templates_data:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug})))
        group = response.context['group']
        self.assertIsInstance(group, Group)
        self.assertEqual(group, self.group)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self.assertEqual(Post.objects.count(), 1)
        self.assertIsInstance(post, Post)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)

    def test_post_detail_list_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.pk})))
        post_detail = response.context['posts']
        self.assertIsInstance(post_detail, Post)
        self.assertEqual(post_detail.author, self.user)
        self.assertEqual(post_detail.group, self.group)

    def test_user_list_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username})))
        user = response.context['page_obj'][0]
        self.assertIsInstance(user, Post)
        self.assertEqual(user.author, self.user)
        self.assertEqual(user.group, self.group)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_cache_index_page(self):
        """Проверка сохранения кэша для index."""
        new_post = Post.objects.create(
            author=self.user,
            text='Проверка кэша'
        )
        response = self.authorized_client.get(reverse('posts:index')).content
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
        self.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test2',
            description='Тестовое описание 2',
        )
        group_list_url2 = reverse(
            'posts:group_list', kwargs={'slug': f'{self.group2.slug}'}
        )
        response = self.authorized_client.get(group_list_url2)
        self.assertEqual(len(response.context['page_obj']), 0)
        group = response.context['group']
        self.assertIsInstance(group, Group)
        self.assertEqual(group, self.group2)

    def test_paginator(self):
        cache.clear()
        Post.objects.bulk_create(
            Post(
                author=self.user,
                text=f'{i + 1} test',
                group=self.group
            )
            for i in range(1, 11)
        )
        for url in [
            INDEX_URL,
            GROUP_LIST_URL,
            PROFILE_URL
        ]:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']), 10
                )
                response_second = self.authorized_client.get(
                    f'{url}?page=2'
                )
                self.assertEqual(
                    len(response_second.context['page_obj']), 1
                )


class FollowTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='FollowUser')
        cls.author = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title='Test Group',
            slug='FollowSlug',
            description='TestDescr'
        )
        cls.post = Post.objects.create(
            text='Test Text Follow',
            author=cls.user,
            group=cls.group
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_follow_authorized_author(self):
        """Проверка, что авторизованный пользователь может подписаться."""
        cache.clear()
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={
                'username': self.author.username
            })
        )
        self.assertTrue(
            Follow.objects.filter(user=self.user, author=self.author).exists()
        )
        # follow = Follow.objects.latest('id')
        # self.assertEqual(follow.user, self.user)
        # self.assertEqual(follow.author, self.author)
        # self.assertRedirects(
        #     response, reverse('posts:profile',
        #                       kwargs={'username': self.author.username}))

    def test_unfollow_authorized_author(self):
        """Проверка, что авторизованный пользователь может отписаться."""
        Follow.objects.create(
            user=self.user, author=self.author
        )
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author.username})
        )
        self.assertEqual(Follow.objects.count(), 0)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user, author=self.author
            ).exists()
        )
        # self.assertRedirects(
        #     response, reverse('posts:profile',
        #                       kwargs={'username': self.author.username}))

    def test_correct_context_follow(self):
        """Проверка, что новая запись появляется у подписчиков."""
        Post.objects.create(
            author=self.author,
            text='NNNN',
        )
        Follow.objects.create(
            user=self.user,
            author=self.author
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertEqual(response.context['page_obj'][0].author, self.author)

    def test_context_unfollow(self):
        """Проверка, что у пользователя не появляется запись,
         тех на кого он не подписан."""
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response.context['page_obj']), 0)
        self.assertNotContains(response, self.post)
