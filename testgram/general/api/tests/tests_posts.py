from django.utils.timezone import make_naive
from rest_framework import status
from rest_framework.test import APITestCase

from general.factories import UserFactory, PostFactory, ReactionFactory
from general.models import Post, Reaction


class PostTestCase(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.url = "/api/posts/"

    def test_create_post(self):
        data = {
            "title": "Test 1",
            "body": "Body 1",
        }

        response = self.client.post(path=self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        post = Post.objects.last()
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.title, data["title"])
        self.assertEqual(post.body, data["body"])
        self.assertIsNotNone(post.created_at)

    def test_unauthorized_post_request(self):
        self.client.logout()
        data = {
            "title": "Test 1",
            "body": "Body 1",
        }
        response = self.client.post(path=self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Post.objects.count(), 0)

    def test_post_list(self):
        PostFactory.create_batch(5)

        response = self.client.get(path=self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)

    def test_post_list_data_structure(self):
        post = PostFactory()
        response = self.client.get(path=self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        author = post.author
        expected_data = {
            "id": post.pk,
            "author": {
                "id": author.pk,
                "first_name": author.first_name,
                "last_name": author.last_name,
            },
            "title": post.title,
            "body": (post.body[:125] + "..." if len(post.body) > 128 else post.body),
            "created_at": make_naive(post.created_at).strftime("%Y-%m-%dT%H:%M:%S"),
        }

        self.assertDictEqual(expected_data, response.data["results"][0])

        post.body = post.body[:125]
        post.save()
        expected_data["body"] = post.body

        response = self.client.get(path=self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(expected_data, response.data["results"][0])

    def test_post_list_logout(self):
        PostFactory.create_batch(5)
        self.client.logout()
        response = self.client.get(path=self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_post_structure(self):
        post = PostFactory()
        author = post.author
        reaction = ReactionFactory(
            author=self.user, post=post, value=Reaction.Values.HEART
        )
        response = self.client.get(path=f"{self.url}{post.pk}/", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = {
            "id": post.pk,
            "author": {
                "id": author.pk,
                "first_name": author.first_name,
                "last_name": author.last_name,
            },
            "title": post.title,
            "body": post.body,
            "my_reaction": reaction.value,
            "created_at": make_naive(post.created_at).strftime("%Y-%m-%dT%H:%M:%S"),
        }
        self.assertDictEqual(expected_data, response.data)

    def test_retrieve_post_structure_without_own_reaction(self):
        target_user = UserFactory()
        post = PostFactory()
        author = post.author
        reaction = ReactionFactory(
            author=target_user, post=post, value=Reaction.Values.SAD
        )
        response = self.client.get(path=f"{self.url}{post.pk}/", format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["my_reaction"], "")

    def test_retrieve_post_logout(self):
        post = PostFactory.create()
        self.client.logout()
        response = self.client.get(path=f"{self.url}{post.pk}/", format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_own_post_with_patch(self):
        post = PostFactory(author=self.user)

        post_data = {
            "title": "New title",
            "body": "New body here",
        }
        response = self.client.patch(
            path=f"{self.url}{post.pk}/",
            data=post_data,
            format="json",
        )
        expected_data = {**post_data, "id": post.pk}

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, expected_data)

    def test_update_foreign_post_with_patch(self):
        post = PostFactory(title="old title", body="old body here")
        post_data = {
            "title": "New title",
            "body": "New body here",
        }
        response = self.client.patch(
            path=f"{self.url}{post.pk}/",
            data=post_data,
            format="json",
        )
        expected_data = {**post_data, "id": post.pk}

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotEqual(response.data, expected_data)

    def test_update_post_with_patch_logout(self):
        post = PostFactory()
        self.client.logout()
        post_data = {
            "title": "New title",
            "body": "New body here",
        }
        response = self.client.patch(
            path=f"{self.url}{post.pk}/", data=post_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_own_post_with_put(self):
        post = PostFactory(author=self.user)

        post_data = {
            "title": "New title",
            "body": "New body here",
        }
        response = self.client.put(
            path=f"{self.url}{post.pk}/",
            data=post_data,
            format="json",
        )
        expected_data = {**post_data, "id": post.pk}

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, expected_data)

    def test_update_foreign_post_with_put(self):
        post = PostFactory(title="old title", body="old body here")
        post_data = {
            "title": "New title",
            "body": "New body here",
        }
        response = self.client.put(
            path=f"{self.url}{post.pk}/",
            data=post_data,
            format="json",
        )
        expected_data = {**post_data, "id": post.pk}

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotEqual(response.data, expected_data)

    def test_update_post_with_put_logout(self):
        post = PostFactory()
        self.client.logout()
        post_data = {
            "title": "New title",
            "body": "New body here",
        }
        response = self.client.put(
            path=f"{self.url}{post.pk}/", data=post_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_own_post(self):
        foreign_post = PostFactory()
        post = PostFactory(author=self.user)
        response = self.client.delete(path=f"{self.url}{post.pk}/", format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 1)

    def test_delete_foreign_post(self):
        foreign_post = PostFactory()
        response = self.client.delete(
            path=f"{self.url}{foreign_post.pk}/", format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Post.objects.count(), 1)

    def test_delete_post_logout(self):
        post = PostFactory()
        self.client.logout()
        response = self.client.delete(path=f"{self.url}{post.pk}/", format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Post.objects.count(), 1)
