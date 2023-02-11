from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Follow, Group, Post, User


def get_page(posts, request):
    paginator = Paginator(posts, settings.MAX_RECORDS)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)


def index(request):
    posts = Post.objects.all()
    page_obj = get_page(posts, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Display all posts group."""
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    page_obj = get_page(
        posts,
        request,
    )
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    current_author = get_object_or_404(User, username=username)
    posts = current_author.posts.all()
    following = (request.user.is_authenticated and request.user != username
                 and Follow.objects.filter(
                     user=request.user,
                     author=current_author).exists())
    page_obj = get_page(posts, request)
    context = {
        'author': current_author,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    return render(
        request,
        'posts/post_detail.html',
        {'post': post, 'form': form}
    )


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None,)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    obj = form.save(commit=False)
    obj.author = request.user
    obj.save()
    return redirect('posts:profile', obj.author.username)


@login_required
def post_edit(request, post_id):
    edit_post = get_object_or_404(Post, pk=post_id)
    if request.user != edit_post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        instance=edit_post,
        files=request.FILES or None,
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    template = 'posts/create_post.html'
    context = {'form': form, 'is_edit': True}
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    posts = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = posts
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = get_page(post_list, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=user, author=author)
    if user != author and not is_follower.exists():
        Follow.objects.create(user=user, author=author)
    return redirect(reverse('posts:profile', args=[username]))


@login_required
def profile_unfollow(request, username):
    follower = request.user
    Follow.objects.filter(user=follower, author__username=username).delete()
    return redirect('posts:profile', username=username)
