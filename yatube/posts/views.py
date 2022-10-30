from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page


from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


LENGTH = 10


def get_page_context(queryset, request):
    return Paginator(queryset, LENGTH).get_page(request.GET.get('page'))


@cache_page(20 * 15)
def index(request):
    return render(request, 'posts/index.html', {
        'page_obj': get_page_context(Post.objects.all(), request),
    })


def group_posts(request, slug):
    group: str = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': get_page_context(
            group.posts.select_related('author'), request),
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    return render(request, 'posts/profile.html', {
        'author': author,
        'page_obj': get_page_context(author.posts.all(), request),
    })


def post_detail(request, post_id):
    form = CommentForm(request.POST or None)
    related = Post.objects.select_related('author', 'group')
    post = get_object_or_404(related, pk=post_id)
    comments = Comment.objects.filter(post=post)
    post_count = post.author.posts.count()
    context = {
        'post': post,
        "post_count": post_count,
        "form": form,
        "comments": comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', username=post.author)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post or None)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/create_post.html', {
        'form': form,
        'is_edit': True,
        'post_id': post_id,
    })


@login_required
def add_comment(request, post_id):
    # Получите пост
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, id=post_id)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    posts = Post.objects.filter(author__following__user=request.user)
    context = {
        "page_obj": get_page_context(posts, request),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    # Подписаться на автора
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect("posts:follow_index")


@login_required
def profile_unfollow(request, username):
    # Дизлайк, отписка
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect("posts:follow_index")
