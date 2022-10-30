from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group, User


class PostFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username='Abramow_test')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def test_create_post(self):
        """Валидная форма создала запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=form_data, follow=True
        )
        self.assertRedirects(
            response, reverse('posts:profile', kwargs={
                'username': self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(text=form_data['text']).exists())

        new_post = Post.objects.last()
        self.assertEqual(new_post.author, self.user)
        self.assertEqual(new_post.group, self.group)

    def test_post_edit(self):
        """Валидная форма изменила запись в Post."""
        text = 'измененный текст'
        self.post = Post.objects.create(
            author=self.user,
            text='Текст для теста',
        )
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        posts_count = Post.objects.count()
        form_data = {'text': 'Изменяем текст', 'group': self.group.id}
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=({self.post.id})),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', kwargs={
                'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=self.group.id,
            pk=self.post.pk,
        ).exists()
        )

        self.assertFalse(Post.objects.filter(
            text=text,
            group=self.group.id,
        ).exists()
        )

    def test_new_post_with_image_created_in_db(self):
        """Проверка сохранения в БД нового поста с картинкой"""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif', content=small_gif, content_type='image/gif'
        )
        form_data = {
            'text': 'Test post with image',
            'image': uploaded,
            'group': self.group.id
        }
        posts_count = Post.objects.count()
        self.authorized_client.post(
            reverse('posts:post_create'), data=form_data
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                author=self.user, text=form_data['text']
            ).exists()
        )

        new_post = Post.objects.last()
        self.assertEqual(new_post.author, self.user)
        self.assertEqual(new_post.group, self.group)
