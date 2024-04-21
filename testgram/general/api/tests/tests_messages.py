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
        self.assertEqual(message.chat, chat)
        self.assertEqual(message.content, data["content"])

    def test_try_to_create_message_for_other_chat(self):
        chat = ChatFactory()
        msg = MessageFactory.create_batch(5, chat=chat)
        data = {
            "chat": chat.pk,
            "content": "message"
        }

        response = self.client.post(path=self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Message.objects.count(), 5)

    def test_delete_own_message(self):
        chat = ChatFactory(user_1=self.user)
        message = MessageFactory(chat=chat, author=self.user)

        response = self.client.delete(path=f"{self.url}{message.pk}/", format="json")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Message.objects.count(), 0)

    def test_delete_other_message(self):
        companion = UserFactory()
        chat = ChatFactory(user_1=self.user, user_2=companion)
        message = MessageFactory(chat=chat, author=companion)

        response = self.client.delete(path=f"{self.url}{message.pk}/", format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Message.objects.count(), 1)
