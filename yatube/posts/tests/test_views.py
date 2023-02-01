from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, Follow

User = get_user_model()


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='tigr')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
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

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            (reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.pk}'
                        })): 'posts/post_detail.html',
            (reverse(
                'posts:group_list',
                kwargs={'slug': f'{self.post.group.slug}'
                        })): 'posts/group_list.html',
            (reverse(
                'posts:profile',
                kwargs={'username': f'{self.post.author}'
                        })): 'posts/profile.html',
            (reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post.pk}'
                        })): 'posts/create_post.html',

        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                cache.clear()
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': 'test_slug'})))
        group = response.context['page_obj'][0].group.title
        self.assertEqual(group, 'Тестовая группа')

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0].text
        self.assertEqual(post, 'Тестовый текст')

    def test_post_detail_list_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': '1'})))
        post_detail = response.context['posts'].text
        self.assertEqual(post_detail, 'Тестовый текст')

    def test_user_list_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': 'tigr'})))
        user = response.context['page_obj'][0].author
        self.assertEqual(user, self.user)

    def test_cache_index_page(self):
        """Проверка сохранения кэша для index."""
        new_post = Post.objects.create(
            author=self.user,
            text='Проверка кэша'
        )
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertIn(new_post, response.context['page_obj'])
        new_post.delete()
        new_response = self.client.get(reverse('posts:index'))
        self.assertEqual(response.content, new_response.content)


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
        response = self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={
                'username': self.author.username
            })
        )
        self.assertTrue(
            Follow.objects.filter(user=self.user, author=self.author).exists()
        )
        follow = Follow.objects.latest('id')
        self.assertEqual(follow.user, self.user)
        self.assertEqual(follow.author, self.author)
        self.assertRedirects(
            response, reverse('posts:profile',
                              kwargs={'username': self.author.username}))

    def test_unfollow_authorized_author(self):
        """Проверка, что авторизованный пользователь может отписаться."""
        Follow.objects.create(
            user=self.user, author=self.author
        )
        response = self.authorized_client.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author.username})
        )
        self.assertEqual(Follow.objects.count(), 0)
        self.assertRedirects(
            response, reverse('posts:profile',
                              kwargs={'username': self.author.username}))

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

    def test_correct_context_unfollow(self):
        """Проверка, что у пользователя не появляется запись,
         тех на кого он не подписан."""
        Post.objects.create(
            author=self.author,
            text='ASDA'
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(len(response.context['page_obj']), 0)
