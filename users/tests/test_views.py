from django.contrib.auth import get_user_model
from django.test import TestCase

from projects.models import Project

user_model = get_user_model()


class DevelopersViewsTest(TestCase):
    def setUp(self):
        self.user = user_model.objects.create_user(
            username="testuser", password="pass"
        )

        self.project1 = Project.objects.create(
            name="Alpha Project",
            owner=self.user,
            development_stage="initiation",
            domain="technology",
        )
        self.project2 = Project.objects.create(
            name="Beta Project",
            owner=self.user,
            development_stage="planning",
            domain="marketing",
        )

        self.client.force_login(self.user)

    def test_profile_view(self):
        response = self.client.get(f"/profile/{self.user.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)
        self.assertContains(response, "Alpha Project")
        self.assertContains(response, "Beta Project")
