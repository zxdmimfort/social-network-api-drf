from django.contrib.auth.hashers import check_password
from django.utils.timezone import make_naive
from rest_framework import status
from rest_framework.test import APITestCase

from general.factories import UserFactory, PostFactory
from general.models import User


class UserTestCase(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.url = "/api/users/"

    def test_user_list(self):
        UserFactory.create_batch(20)

        response = self.client.get(path=self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertEqual(response.data["count"], 21)

    def test_user_list_response_structure(self):
        response = self.client.get(path=self.url, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        expected_data = {
            "id": self.user.pk,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "is_friend": False,
        }
        self.assertDictEqual(response.data["results"][0], expected_data)

    def test_user_list_is_friend_field(self):
        users = UserFactory.create_batch(5)

        self.user.friends.add(users[-1])
        self.user.save()

        with self.assertNumQueries(3):
            response = self.client.get(path=self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 6)

        self.assertTrue(response.data["results"][0]["is_friend"])
        for user_data in response.data["results"][1:]:
            self.assertFalse(user_data["is_friend"])

    def test_user_list_logout(self):
        self.client.logout()
        UserFactory.create_batch(5)
        response = self.client.get(path=self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_correct_registration(self):
        self.client.logout()

        data = {
            "username": "test_user_1",
            "password": "12345",
            "email": "test_user_1@gmail.com",
            "first_name": "John",
            "last_name": "Smith",
        }
        response = self.client.post(path=self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_user = User.objects.last()
        self.assertTrue(check_password(data["password"], created_user.password))
        data.pop("password")

        user_data = {
            "username": created_user.username,
            "email": created_user.email,
            "first_name": created_user.first_name,
            "last_name": created_user.last_name,
        }
        self.assertDictEqual(data, user_data)

    def test_try_to_pass_existing_username(self):
        self.client.logout()

        data = {
            "username": self.user.username,
            "password": "12345",
            "email": "test_user_1@gmail.com",
            "first_name": "John",
            "last_name": "Smith",
        }

        response = self.client.post(path=self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.all().count(), 1)

    def test_user_add_friend(self):
        friend = UserFactory()

        url = f"{self.url}{friend.pk}/add_friend/"
        response = self.client.post(path=url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(friend in self.user.friends.all())

    def test_user_add_friends_logout(self):
        self.client.logout()
        friend = UserFactory()
        response = self.client.post(
            path=f"{self.url}{friend.pk}/add_friend/", format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_add_request_with_existent_friend(self):
        friend = UserFactory()
        self.user.friends.add(friend)
        self.user.save()

        url = f"{self.url}{friend.pk}/add_friend/"
        response = self.client.post(path=url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(friend in self.user.friends.all())

    def test_user_remove_friend(self):
        friend = UserFactory()
        self.user.friends.add(friend)
        self.user.save()

        url = f"{self.url}{friend.pk}/remove_friend/"
        response = self.client.post(path=url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(friend in self.user.friends.all())

    def test_user_remove_friend_logout(self):
        friend = UserFactory()
        self.client.logout()
        response = self.client.post(
            path=f"{self.url}{friend.pk}/remove_friend/", format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_remove_friend_with_non_existent_friend(self):
        friend = UserFactory()
        url = f"{self.url}{friend.pk}/remove_friend/"

        response = self.client.post(path=url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(friend in self.user.friends.all())

    def test_retrieve_user(self):
        target_user = UserFactory()

        # friends
        target_user.friends.add(self.user)
        target_user.friends.add(UserFactory())
        target_user.save()

        # posts
        post_1 = PostFactory(author=target_user, title="Post 1")
        post_2 = PostFactory(author=target_user, title="Post 2")

        # other posts
        PostFactory.create_batch(10)

        response = self.client.get(path=f"{self.url}{target_user.pk}/", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = {
            "id": target_user.pk,
            "first_name": target_user.first_name,
            "last_name": target_user.last_name,
            "email": target_user.email,
            "is_friend": True,
            "friend_count": 2,
            "posts": [
                {
                    "id": post_1.pk,
                    "title": post_1.title,
                    "body": post_1.body,
                    "created_at": make_naive(post_1.created_at).strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    ),
                },
                {
                    "id": post_2.pk,
                    "title": post_2.title,
                    "body": post_2.body,
                    "created_at": make_naive(post_2.created_at).strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    ),
                },
            ],
        }

        self.assertEqual(expected_data, response.data)

    def test_retrieve_user_logout(self):
        target_user = UserFactory()
        self.client.logout()
        response = self.client.get(path=f"{self.url}{target_user.pk}/", format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_user_friends(self):
        target_user = UserFactory()

        friends = UserFactory.create_batch(3)
        target_user.friends.set(friends)
        target_user.save()

        UserFactory.create_batch(5)
        url = f"{self.url}{target_user.pk}/friends/"
        response = self.client.get(path=url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

        friends_ids = {user.pk for user in friends}
        for friend in response.data["results"]:
            self.assertTrue(friend["id"] in friends_ids)

    def test_get_user_friends_response_data_structure(self):
        target_user = UserFactory()
        friend = UserFactory()
        target_user.friends.add(friend)
        target_user.save()

        url = f"{self.url}{target_user.pk}/friends/"
        response = self.client.get(path=url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

        expected_data = {
            "id": friend.pk,
            "first_name": friend.first_name,
            "last_name": friend.last_name,
            "is_friend": False,
        }

        self.assertDictEqual(expected_data, response.data["results"][0])

    def test_get_friends_logout(self):
        self.client.logout()
        target_user = UserFactory()
        friends = UserFactory.create_batch(5)
        target_user.friends.set(friends)
        target_user.save()
        response = self.client.get(f"{self.url}{target_user}/friends/", format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_me(self):
        target_user = UserFactory()
        self.client.force_authenticate(user=target_user)

        # friends
        target_user.friends.add(self.user)
        target_user.friends.add(UserFactory())
        target_user.save()

        # posts
        post_1 = PostFactory(author=target_user, title="Post 1")
        post_2 = PostFactory(author=target_user, title="Post 2")

        # other posts
        PostFactory.create_batch(10)

        response = self.client.get(
            path=f"{self.url}me/",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_data = {
            "id": target_user.pk,
            "first_name": target_user.first_name,
            "last_name": target_user.last_name,
            "email": target_user.email,
            "is_friend": False,
            "friend_count": 2,
            "posts": [
                {
                    "id": post_1.pk,
                    "title": post_1.title,
                    "body": post_1.body,
                    "created_at": make_naive(post_1.created_at).strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    ),
                },
                {
                    "id": post_2.pk,
                    "title": post_2.title,
                    "body": post_2.body,
                    "created_at": make_naive(post_2.created_at).strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    ),
                },
            ],
        }

        self.assertDictEqual(response.data, expected_data)

    def test_get_me_logout(self):
        self.client.logout()
        response = self.client.get(path=f"{self.url}me/", format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
