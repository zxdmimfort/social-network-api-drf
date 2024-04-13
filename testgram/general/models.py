from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import F, functions
from rest_framework.authtoken.models import Token


class User(AbstractUser):
    friends = models.ManyToManyField(
        to="self",
        symmetrical=True,
        blank=True,
    )


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=64)
    body = models.TextField()
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(auto_now=True)


class Comment(models.Model):
    body = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    created_at = models.DateTimeField(auto_now_add=True)
    updated = models.BooleanField(default=False)


class Reaction(models.Model):
    class Values(models.TextChoices):
        SMILE = "smile", "Улыбка"
        THUMB_UP = "thumb_up", "Большой палец вверх"
        LAUGH = "laugh", "Смех"
        SAD = "sad", "Грусть"
        HEART = "heart", "Сердце"

    value = models.CharField(max_length=8, choices=Values.choices, null=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reactions")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="reactions")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                "author",
                "post",
                name="author_post_unique",
            ),
        ]


class Chat(models.Model):
    user_1 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chats_as_user1"
    )
    user_2 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="chats_as_user2"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                functions.Greatest(F("user_1"), F("user_2")),
                functions.Least(F("user_1"), F("user_2")),
                name="users_chat_unique",
            ),
        ]


class Message(models.Model):
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    created_at = models.DateTimeField(auto_now_add=True)
    updated = models.BooleanField(default=False)
