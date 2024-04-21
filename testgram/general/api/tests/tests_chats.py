from django.utils.timezone import make_naive
from rest_framework import status
from rest_framework.test import APITestCase

from general.factories import UserFactory, ChatFactory, MessageFactory
from general.models import Chat, Message


class ChatTestCase(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.url = "/api/chats/"

    def test_get_chat_list(self):
        users = UserFactory.create_batch(3)
        chats = [
            ChatFactory(user_1=users[0], user_2=self.user),
            ChatFactory(user_1=users[1], user_2=self.user),
            ChatFactory(user_1=self.user, user_2=users[2]),
        ]

        mes_2 = MessageFactory(author=self.user, chat=chats[2])
        mes_0 = MessageFactory(author=self.user, chat=chats[0])
        mes_1 = MessageFactory(author=users[1], chat=chats[1])

        MessageFactory.create_batch(10)
        with self.assertNumQueries(2):
            response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

        response_chat_ids = [chat["id"] for chat in response.data["results"]]
        expected_chat_ids = [chats[1].pk, chats[0].pk, chats[2].pk]
        self.assertListEqual(response_chat_ids, expected_chat_ids)

        chat_0_expected = {
            "id": chats[0].pk,
            "companion_name": f"{chats[0].user_1.first_name} {chats[0].user_1.last_name}",
            "last_message_content": mes_0.content,
            "last_message_datetime": make_naive(mes_0.created_at).strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),
            "last_message_author": "Вы",
        }
        chat_1_expected = {
            "id": chats[1].pk,
            "companion_name": f"{chats[1].user_1.first_name} {chats[1].user_1.last_name}",
            "last_message_content": mes_1.content,
            "last_message_datetime": make_naive(mes_1.created_at).strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),
            "last_message_author": f"{users[1].first_name} {users[1].last_name}",
        }

        chat_2_expected = {
            "id": chats[2].pk,
            "companion_name": f"{chats[2].user_2.first_name} {chats[2].user_2.last_name}",
            "last_message_content": mes_2.content,
            "last_message_datetime": make_naive(mes_2.created_at).strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),
            "last_message_author": "Вы",
        }

        self.assertDictEqual(chat_0_expected, response.data["results"][1])
        self.assertDictEqual(chat_1_expected, response.data["results"][0])
        self.assertDictEqual(chat_2_expected, response.data["results"][2])

    def test_get_all_chats(self):
        chats = ChatFactory.create_batch(5, user_1=self.user)
        msgs = []
        for chat in chats[1:]:
            msgs.append(MessageFactory(chat=chat))

        response = self.client.get(path=f"{self.url}?empty=0", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(msgs), response.data["count"])

        response = self.client.get(path=f"{self.url}", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(chats), response.data["count"])

        response = self.client.get(path=f"{self.url}?empty=1", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(chats) - len(msgs), response.data["count"])

    def test_create_chat(self):
        user = UserFactory()
        data = {"user_2": user.pk}
        response = self.client.post(path=self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        chat = Chat.objects.last()
        expected_data = {
            "id": chat.pk,
            "companion_id": chat.user_2.pk,
        }
        self.assertDictEqual(response.data, expected_data)
        self.assertEqual(chat.user_1, self.user)

    def test_try_to_create_chat_when_exists(self):
        user = UserFactory()
        data = {"user_2": user.pk}
        chat = ChatFactory(user_1=self.user, user_2=user)

        response = self.client.post(path=self.url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Chat.objects.count(), 1)
        expected_data = {
            "id": chat.pk,
            "companion_id": chat.user_2.pk,
        }
        self.assertDictEqual(expected_data, response.data)

        self.client.force_authenticate(user=user)
        data = {"user_2": self.user.pk}

        response = self.client.post(path=self.url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Chat.objects.count(), 1)
        expected_data = {
            "id": chat.pk,
            "companion_id": self.user.pk,
        }
        self.assertDictEqual(expected_data, response.data)

    def test_delete_chat(self):
        chat_1 = ChatFactory(user_1=self.user)
        chat_2 = ChatFactory(user_2=self.user)

        MessageFactory(author=self.user, chat=chat_1)
        MessageFactory(author=self.user, chat=chat_2)

        response = self.client.delete(f"{self.url}{chat_1.pk}/", format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.delete(f"{self.url}{chat_2.pk}/", format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertEqual(Chat.objects.count(), 0)
        self.assertEqual(Message.objects.all().count(), 0)

    def test_try_to_delete_other_chat(self):
        chat = ChatFactory()

        response = self.client.delete(f"{self.url}{chat.pk}/", format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertEqual(Chat.objects.count(), 1)

    def test_get_messages(self):
        user = UserFactory()
        chat = ChatFactory(user_1=self.user, user_2=user)

        message_1 = MessageFactory(author=self.user, chat=chat)
        message_2 = MessageFactory(author=user, chat=chat)
        message_3 = MessageFactory(author=self.user, chat=chat)

        url = f"{self.url}{chat.pk}/messages/"

        with self.assertNumQueries(2):
            response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

        # сообщения приходят в порядке от новых к старым.
        # поэтому сначала проверяем message_3.
        message_3_expected_data = {
            "id": message_3.pk,
            "content": message_3.content,
            "message_author": "Вы",
            "created_at": make_naive(message_3.created_at).strftime(
                ("%Y-%m-%dT%H:%M:%S")
            ),
        }
        self.assertDictEqual(
            response.data[0],
            message_3_expected_data,
        )

        message_2_expected_data = {
            "id": message_2.pk,
            "content": message_2.content,
            "message_author": user.first_name,
            "created_at": make_naive(message_2.created_at).strftime(
                ("%Y-%m-%dT%H:%M:%S")
            ),
        }
        self.assertDictEqual(
            response.data[1],
            message_2_expected_data,
        )

        message_1_expected_data = {
            "id": message_1.pk,
            "content": message_1.content,
            "message_author": "Вы",
            "created_at": make_naive(message_1.created_at).strftime(
                ("%Y-%m-%dT%H:%M:%S")
            ),
        }
        self.assertDictEqual(
            response.data[2],
            message_1_expected_data,
        )

    def test_get_messages_from_foreign_chat(self):
        (user1, user2) = UserFactory.create_batch(2)
        chat = ChatFactory(user_1=user1, user_2=user2)
        message_1 = MessageFactory(author=user1, chat=chat)
        message_2 = MessageFactory(author=user2, chat=chat)

        response = self.client.get(path=f"{self.url}{chat.pk}/messages/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
