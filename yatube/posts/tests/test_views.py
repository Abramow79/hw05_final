import shutil
import tempfile

from django import forms

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Follow, Group, Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        cls.user = User.objects.create(username="Abramow_test")
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый пост",
            group=cls.group,
            image=uploaded,
        )
        cls.templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_posts",
                kwargs={"slug": cls.group.slug}
            ): "posts/group_list.html",
            reverse(
                "posts:profile",
                kwargs={"username": cls.post.author}
            ): "posts/profile.html",
            reverse(
                "posts:post_detail",
                kwargs={"post_id": cls.post.id}
            ): "posts/post_detail.html",
            reverse(
                "posts:post_edit",
                kwargs={"post_id": cls.post.id}
            ): "posts/create_post.html",
            reverse("posts:post_create"): "posts/create_post.html",
        }
        cls.DETAIL_URL = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.id}
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(template)
                self.assertTemplateUsed(response, reverse_name)

    def test_index_show_correct_context(self):
        """Список постов в шаблоне index равен ожидаемому контексту."""
        response = self.client.get(reverse("posts:index"))
        expected = list(Post.objects.all()[:10])
        self.assertEqual(list(response.context["page_obj"]), expected)

    def test_group_list_show_correct_context(self):
        """Список постов в шаблоне group_list равен ожидаемому контексту"""
        context = self.client.get(
            reverse("posts:group_posts", kwargs={"slug": self.group.slug})
        ).context
        first_object = context["page_obj"][0]
        self.assertEqual(context["group"], self.group)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.image, self.post.image)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        context = self.authorized_client.get(
            reverse("posts:profile", kwargs={"username": self.post.author})
        ).context
        first_object = context["page_obj"][0]
        self.assertEqual(context["author"], self.post.author)
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.image, self.post.image)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        first_object = self.client.get(reverse("posts:index")).context[
            "page_obj"
        ][0]
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.image, self.post.image)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.client.get(
            reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        )
        self.assertEqual(response.context.get("post").text, self.post.text)
        self.assertEqual(response.context.get("post").id, self.post.id)
        self.assertEqual(response.context.get("post").author, self.post.author)
        self.assertEqual(response.context.get("post").group, self.post.group)
        self.assertEqual(response.context.get("post").image, self.post.image)

    def test_create_edit_show_correct_context(self):
        """Шаблон create_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse("posts:post_edit", kwargs={"post_id": self.post.id})
        )
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse("posts:post_create"))
        form_fields = {
            "text": forms.fields.CharField,
            "group": forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_check_group_in_pages(self):
        """Проверяем создание поста на страницах с выбранной группой"""
        form_fields = {
            reverse("posts:index"): Post.objects.get(group=self.post.group),
            reverse(
                "posts:group_posts", kwargs={"slug": self.group.slug}
            ): Post.objects.get(group=self.post.group),
            reverse(
                "posts:profile", kwargs={"username": self.post.author}
            ): Post.objects.get(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertIn(expected, form_field)

    def test_check_group_not_in_mistake_group_list_page(self):
        """Проверяем чтобы созданный Пост с группой не попап в чужую группу."""
        form_fields = {
            reverse(
                "posts:group_posts",
                kwargs={"slug": self.group.slug}
            ): Post.objects.exclude(group=self.post.group),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertNotIn(expected, form_field)

    def test_new_comment(self):
        """Проверка появления нового комментария на странице поста."""
        COMMENT_TEXT = 'Комментприй тестовый'
        count_of_comments = Comment.objects.filter(post=self.post).count()
        Comment.objects.create(
            post=self.post,
            text=COMMENT_TEXT,
            author=self.user,
        )
        response = self.client.get(self.DETAIL_URL)
        self.assertEqual(
            response.context['comments'].count(),
            count_of_comments + 1,
            'На странице поста не появился новый комментарий'
        )


class PostPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Abramow_test')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.INDEX_URL = reverse('posts:index')
        cls.GROUP_LIST_URL = reverse(
            'posts:group_posts', kwargs={'slug': f'{cls.group.slug}'}
        )
        cls.PROFILE_URL = reverse(
            'posts:profile', kwargs={'username': f'{cls.author.username}'}
        )
        cls.ADDPOSTS = 5

        cls.posts = Post.objects.bulk_create(
            Post(
                author=cls.author,
                text=f'{i + 1} длинный тестовый пост',
                group=cls.group
            )
            for i in range(settings.POSTS_PER_PAGE + cls.ADDPOSTS)
        )

    def test_accordance_posts_per_pages(self):
        """Проверяем, что количество постов
        на первой странице равно 10, а на второй - 5"""

        for url in [
            PostPaginatorTests.INDEX_URL,
            PostPaginatorTests.GROUP_LIST_URL,
            PostPaginatorTests.PROFILE_URL
        ]:
            with self.subTest(url=url):
                response = PostPaginatorTests.author_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.POSTS_PER_PAGE
                )
                response_second = PostPaginatorTests.author_client.get(
                    f'{url}?page=2'
                )
                self.assertEqual(
                    len(response_second.context['page_obj']),
                    PostPaginatorTests.ADDPOSTS
                )


class FollowViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username="Тестовый автор")
        cls.user = User.objects.create_user(username="Тестовый юзер")
        cls.following_user = User.objects.create_user(username="Подписчик")

    def setUp(self):
        self.user_client = Client()
        self.user_client.force_login(self.user)
        self.following_user_client = Client()
        self.following_user_client.force_login(self.following_user)

    def test_user_can_follow_and_unfollow(self):
        """Проверка того, что авторизованный пользователь может подписываться и
        отписываться от автора"""
        self.user_client.get(
            reverse("posts:profile_follow", kwargs={"username": self.author})
        )
        self.assertTrue(
            Follow.objects.filter(user=self.user, author=self.author).exists()
        )
        self.user_client.get(
            reverse("posts:profile_unfollow", kwargs={"username": self.author})
        )
        self.assertFalse(
            Follow.objects.filter(user=self.user, author=self.author).exists()
        )

    def test_new_post_correct_mapping(self):
        """Проверка, что новый пост появляется у подписчиков автора и
        не появляется у тех в ленте, кто не подписан на автора"""
        Follow.objects.create(author=self.author, user=self.following_user)
        post = Post.objects.create(author=self.author, text="Test post")
        response = self.following_user_client.get(
            reverse("posts:follow_index")
        )
        self.assertTrue(post in response.context["page_obj"])
        response = self.user_client.get(reverse("posts:follow_index"))
        self.assertFalse(post in response.context["page_obj"])
