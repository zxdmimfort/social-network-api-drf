from rest_framework import status
from rest_framework.test import APITestCase

from general.factories import UserFactory, ChatFactory, MessageFactory
from general.models import Message


class MessageTestCase(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.url = "/api/messages/"

    def test_create_messages(self):
        chat = ChatFactory(user_1=self.user)
        data = {
            "chat": chat.pk,
            "content": "Who is here?",
        }

        response = self.client.post(path=self.url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["chat"], chat.pk)
        self.assertIsNotNone(response.data["created_at"])
        self.assertEqual(response.data["content"], data["content"])
        message = Message.objects.last()
        self.assertEqual(message.author, self.user)
        self.assertEqual()
