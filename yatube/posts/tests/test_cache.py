from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post

User = get_user_model()


class PostCacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="Abramow")
        cls.post = Post.objects.create(
            author=cls.user,
            text="Test post",
        )
        objs = (Post(author=cls.user, text="Test post") for _ in range(3))
        Post.objects.bulk_create(objs)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_new_post_not_in_cache(self):
        """Проверка: удаленный пост остается в кэше"""
        post_1 = Post.objects.create(author=self.user, text="Post_1")
        response_1 = self.authorized_client.get(reverse("posts:index"))
        self.assertEqual(response_1.context["page_obj"][0], post_1)
        Post.objects.filter(pk=post_1.id).delete()
        response_2 = self.authorized_client.get(reverse("posts:index"))
        self.assertEqual(response_1.content, response_2.content)
        cache.clear()
        response_3 = self.authorized_client.get(reverse("posts:index"))
        self.assertNotEqual(
            post_1,
            response_3.context["page_obj"][0],
            'Удаленного поста нет в кэше'
        )


class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Abramow')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
        )

    def test_cache_index(self):
        """Проверка работы кэша на главной странице."""
        INDEX_URL = reverse('posts:index')
        response = self.authorized_client.get(INDEX_URL)
        self.post.delete()
        response2 = self.authorized_client.get(INDEX_URL)
        self.assertEqual(
            response.content,
            response2.content,
            'Кэш главной страницы работает неверно',
        )
        cache.clear()
        response3 = self.authorized_client.get(INDEX_URL)
        self.assertNotEqual(
            response.content,
            response3.content,
            'Кэш не очистился или работает неверно'
        )
