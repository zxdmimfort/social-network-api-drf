from django.utils.timezone import make_naive
from rest_framework import status
from rest_framework.test import APITestCase

from general.factories import PostFactory, UserFactory, CommentFactory
from general.models import Comment


class CommentTestCase(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
        self.post = PostFactory()
        self.url = "/api/comments/"

    def test_create_comment(self):
        data = {
            "post": self.post.pk,
            "body": "comment body",
        }
        response = self.client.post(path=self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        comment = Comment.objects.last()
        self.assertEqual(data["post"], comment.post.id)
        self.assertEqual(data["body"], comment.body)
        self.assertEqual(self.user, comment.author)
        self.assertIsNotNone(comment.created_at)

    def test_pass_incorrect_post_id(self):
        data = {"post": self.post.pk + 1, "body": "comment body"}
        response = self.client.post(path=self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_own_comment(self):
        comment = CommentFactory(post=self.post, author=self.user)
        response = self.client.delete(path=f"{self.url}{comment.pk}/", format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)

    def test_delete_not_own_comment(self):
        comment = CommentFactory(post=self.post)
        response = self.client.delete(path=f"{self.url}{comment.pk}/", format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Comment.objects.count(), 1)

    def test_comment_list_filtered_by_post_id(self):
        comments = CommentFactory.create_batch(5, post=self.post)
        CommentFactory.create_batch(5)

        url = f"{self.url}?post__id={self.post.pk}"
        response = self.client.get(path=url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 5)
        comment_ids = [comment.pk for comment in comments]
        for comment in response.data["results"]:
            self.assertIn(comment["id"], comment_ids)

    def test_comment_data_structure(self):
        comment = CommentFactory(post=self.post)
        response = self.client.get(f"{self.url}?post__id={self.post.pk}", format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = {
            "id": comment.pk,
            "author": {
                "id": comment.author.pk,
                "first_name": comment.author.first_name,
                "last_name": comment.author.last_name,
            },
            "post": comment.post.pk,
            "body": comment.body,
            "created_at": make_naive(comment.created_at).strftime("%Y-%m-%dT%H:%M:%S"),
        }

        self.assertDictEqual(response.data["results"][0], expected_data)
