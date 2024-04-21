from rest_framework import status
from rest_framework.test import APITestCase

from general.factories import UserFactory, PostFactory, ReactionFactory
from general.models import Reaction


class ReactionTestCase(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.url = "/api/reactions/"

    def test_post_reaction(self):
        post = PostFactory()
        data = {
            "value": "smile",
            "post": post.pk,
        }

        response = self.client.post(path=self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        reaction = Reaction.objects.last()
        self.assertDictEqual({**data, "id": reaction.pk}, response.data)

    def test_post_reaction_on_same_post(self):
        post_1 = PostFactory()
        post_2 = PostFactory()
        reaction_1 = ReactionFactory(post=post_1, author=self.user, value="smile")
        reaction_2 = ReactionFactory(post=post_2, author=self.user, value="smile")

        data = {
            "value": "sad",
            "post": post_1.pk,
        }

        response = self.client.post(path=self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertDictEqual({**data, "id": reaction_1.pk}, response.data)

        data = {
            "post": post_2.pk,
            "value": "smile",
        }
        expected_data = {
            "id": reaction_2.pk,
            "post": post_2.pk,
            "value": None,
        }
        response = self.client.post(path=self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertDictEqual(expected_data, response.data)

    def test_post_reaction_with_invalid_value(self):
        post = PostFactory()
        data = {
            "post": post.pk,
            "value": "adsfasdklfasd",
        }

        response = self.client.post(path=self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Reaction.objects.count(), 0)

