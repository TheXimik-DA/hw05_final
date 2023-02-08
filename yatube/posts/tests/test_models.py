from django.test import TestCase

from posts.models import Comment, Follow, Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Auth_user')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )

    def test_models_have_correct_object_names(self):
        """Проверrка корректности работы __str__."""
        post = PostModelTest.post
        expected_post_title = post.text
        self.assertEqual(str(post), expected_post_title[:15])

    def test_models_have_verbose_name(self):
        """Проверяем совпадение verbose_name с ожидаемым"""
        field_verboses = {
            'text': 'Текст поста',
            'group': 'Группа поста',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).verbose_name, expected_value)

    def test_models_have_help_text(self):
        """Проверка help_text"""
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Укажите группу для поста',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    Post._meta.get_field(field).help_text, expected_value)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_models_Group_have_correct_object_names(self):
        """Проверка корректности работы __str__."""
        group = GroupModelTest.group
        expected_group_title = group.title
        self.assertEqual(str(group), expected_group_title)


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Пост для комментария',
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            text='Вежливый комментарий',
            post=cls.post,
        )

    def test_models_have_correct_object_names_comments(self):
        """Проверяем, что у модели Comment корректно работает __str__."""
        comment_text = CommentModelTest.comment
        expected_object_text = comment_text.text[:15]
        self.assertEqual(expected_object_text, str(comment_text))


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.follower = User.objects.create_user(username='follower')
        cls.follow = Follow.objects.create(
            author=cls.author,
            user=cls.follower
        )

    def test_follow_models_have_correct_object_name(self):
        follow = FollowModelTest.follow
        follow = f'{follow.user.username} подписан на {follow.author.username}'
        self.assertEqual(follow, str(follow))

    def test_follow_verbose_name(self):
        follow = FollowModelTest.follow
        field_verboses = {
            'user': 'Подписчик',
            'author': 'Автор',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    follow._meta.get_field(field).verbose_name, expected_value
                )

    def test_follow_help_text(self):
        follow = FollowModelTest.follow
        field_help_texts = {
            'user': 'Это подписчик',
            'author': 'Это автор',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    follow._meta.get_field(field).help_text, expected_value
                )
