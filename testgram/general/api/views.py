from django.db.models import CharField, Case, When, Value, F, OuterRef, Q, Subquery
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from general.api.serializers import (
    UserRegistrationSerializer,
    UserListSerializer,
    UserRetrieveSerializer,
    PostRetrieveSerializer,
    PostCreateSerializer,
    PostListSerializer,
    CommentSerializer,
    ReactionSerializer,
    ChatSerializer,
    MessageListSerializer,
    ChatListSerializer,
    MessageSerializer,
)
from general.models import User, Post, Comment, Message, Chat


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    def get_queryset(self):
        queryset = User.objects.all().prefetch_related("friends").order_by("-id")
        return queryset

    @action(detail=True, methods=["get"])
    def friends(self, request, pk=None):
        user = self.get_object()
        queryset = self.filter_queryset(self.get_queryset().filter(friends=user))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def me(self, request):
        instance = self.request.user
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def add_friend(self, request, pk=None):
        user = self.get_object()
        request.user.friends.add(user)
        return Response("Friend added")

    @action(detail=True, methods=["post"])
    def remove_friend(self, request, pk=None):
        user = self.get_object()
        request.user.friends.remove(user)
        return Response("Friend removed")

    def get_serializer_class(self):
        if self.action == "create":
            return UserRegistrationSerializer
        elif self.action in ("retrieve", "me"):
            return UserRetrieveSerializer
        return UserListSerializer

    def get_permissions(self):
        if self.action == "create":
            self.permission_classes = [AllowAny]
        else:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()


class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.action in ("list"):
            queryset = Post.objects.all().select_related("author").order_by("-id")
        else:
            queryset = Post.objects.all().order_by("-id")
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return PostListSerializer
        elif self.action == "retrieve":
            return PostRetrieveSerializer
        else:
            return PostCreateSerializer

    def perform_update(self, serializer):
        instance = self.get_object()

        if instance.author != self.request.user:
            raise PermissionDenied("Вы не являетесь автором этого поста.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("Вы не являетесь автором этого поста.")
        instance.delete()


class CommentsViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Comment.objects.all().order_by("-id")
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["post__id"]

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("Вы не являетесь автором этого комментария.")
        instance.delete()


class ReactionsViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ReactionSerializer


class ChatViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        response_data = {
            **serializer.data,
            "user_2": serializer.validated_data["user_2"].pk,
        }
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer_class(self):
        if self.action == "list":
            return ChatListSerializer
        elif self.action == "messages":
            return MessageListSerializer
        return ChatSerializer

    def list(self, request, *args, **kwargs):
        empty = request.query_params.get("empty")
        queryset = self.filter_queryset(self.get_queryset(empty))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self, empty: bool | None = None):
        user = self.request.user
        query_param = {}
        if empty is not None:
            query_param["messages__isnull"] = empty

        last_message_subquery = (
            Message.objects.filter(chat=OuterRef("pk"))
            .order_by("-created_at")
            .values("created_at")[:1]
        )
        last_message_content_subquery = (
            Message.objects.filter(chat=OuterRef("pk"))
            .order_by("-created_at")
            .values("content")[:1]
        )
        last_message_author_subquery = (
            Message.objects.filter(chat=OuterRef("pk"))
            .order_by("-created_at")
            .values("author")[:1]
        )

        qs = (
            Chat.objects.filter(Q(user_1=user) | Q(user_2=user), **query_param)
            .annotate(
                last_message_datetime=Subquery(last_message_subquery),
                last_message_content=Subquery(last_message_content_subquery),
                last_message_author=Subquery(last_message_author_subquery),
            )
            .select_related(
                "user_1",
                "user_2",
            )
            .order_by("-last_message_datetime")
            .distinct()
        )

        return qs

    @action(detail=True, methods=["get"])
    def messages(self, request, pk=None):
        messages = (
            self.get_object()
            .messages.filter(chat__id=pk)
            .annotate(
                message_author=Case(
                    When(author=self.request.user, then=Value("Вы")),
                    default=F("author__first_name"),
                    output_field=CharField(),
                )
            )
            .order_by("-created_at")
        )
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)


class MessageViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    queryset = Message.objects.all().order_by("-id")

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("Вы не являетесь автором этого сообщения.")
        instance.delete()
