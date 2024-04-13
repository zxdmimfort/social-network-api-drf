from django.contrib import admin
from django.contrib.auth.models import Group

from general.models import User, Post, Reaction, Comment, Message, Chat

admin.site.register(Chat)
admin.site.unregister(Group)


@admin.register(User)
class UserModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "first_name",
        "last_name",
        "username",
        "email",
        "is_staff",
        "is_superuser",
        "is_active",
        "date_joined",
    )
    readonly_fields = (
        "date_joined",
        "last_login",
    )
    fieldsets = (
        (
            "Личные данные",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                )
            },
        ),
        (
            "Учетные данные",
            {
                "fields": (
                    "username",
                    "password",
                )
            },
        ),
        (
            "Статусы",
            {
                "classes": ("collapse",),
                "fields": (
                    "is_staff",
                    "is_superuser",
                    "is_active",
                ),
            },
        ),
        (None, {"fields": ("friends",)}),
        (
            "Даты",
            {
                "fields": (
                    "date_joined",
                    "last_login",
                )
            },
        ),
    )


@admin.register(Post)
class PostModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "title",
        "get_body",
        "created_at",
        "get_comment_count",
    )
    list_display_links = ("id", "title")

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("comments")

    def get_comment_count(self, obj):
        return obj.comments.count()

    def get_body(self, obj):
        max_length = 64
        if len(obj.body) > max_length:
            return obj.body[:61] + "..."
        return obj.body

    get_body.short_description = "body"
    get_comment_count.short_description = "comment count"


@admin.register(Comment)
class CommentModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "post",
        "body",
        "created_at",
    )
    list_display_links = (
        "id",
        "body",
    )


@admin.register(Reaction)
class ReactionModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "author",
        "post",
        "value",
    )


@admin.register(Message)
class MessageModelAdmin(admin.ModelAdmin):
    list_display = ("chat", "author", "content", "created_at")
    fields = ("content", "author", "chat")
