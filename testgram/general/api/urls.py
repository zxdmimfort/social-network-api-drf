from rest_framework import routers

from general.api.views import (
    UserViewSet,
    PostViewSet,
    CommentsViewSet,
    ReactionsViewSet,
    ChatViewSet,
    MessageViewSet,
)

router = routers.SimpleRouter()
router.register(r"comments", CommentsViewSet, basename="comments")
router.register(r"posts", PostViewSet, basename="posts")
router.register(r"users", UserViewSet, basename="users")
router.register(r"reactions", ReactionsViewSet, basename="reactions")
router.register(r"chats", ChatViewSet, basename="chats")
router.register(r"messages", MessageViewSet, basename="messages")
urlpatterns = router.urls
