from django.contrib.auth import get_user_model
from django.test import TestCase

from projects.models import Project, ProjectMembership, ProjectApplication, ProjectOpenRole, ProjectRating

user_model = get_user_model()


class ModelsTestCase(TestCase):
    def test_project_str(self):
        user = user_model.objects.create(username='testuser', email='<EMAIL>', password='<PASSWORD>')
        project = Project.objects.create(name='Test Project', description='A test project', owner=user)

        self.assertEqual(str(project), project.name)

    def test_get_members(self):
        user_1 = user_model.objects.create(username='testuser', email='<EMAIL>', password='<PASSWORD>')
        user_2 = user_model.objects.create(username='testuser1', email='<EMAIL>', password='<PASSWORD>')
        user_3 = user_model.objects.create(username='testuser2', email='<EMAIL>', password='<PASSWORD>')
        user_4 = user_model.objects.create(username='testuser3', email='<EMAIL>', password='<PASSWORD>')

        project = Project.objects.create(name='Test Project', description='A test project', owner=user_1)

        ProjectMembership.objects.create(project=project, user=user_2, role='DEV')
        ProjectMembership.objects.create(project=project, user=user_3, role='LEAD')
        ProjectMembership.objects.create(project=project, user=user_4, role='PM')

        members = project.get_members()
        expected_members = user_model.objects.filter(pk__in=[user_2.pk, user_3.pk, user_4.pk])

        self.assertSetEqual(set(members), set(expected_members))

    def test_open_to_candidates(self):
        user = user_model.objects.create(username='testuser', email='<EMAIL>', password='<PASSWORD>')
        project = Project.objects.create(name='Test Project', description='A test project', owner=user)

        self.assertFalse(project.open_to_candidates)

        ProjectOpenRole.objects.create(project=project)
        project.update_open_to_candidates()

        self.assertTrue(project.open_to_candidates)

        ProjectOpenRole.objects.filter(project=project).delete()
        project.update_open_to_candidates()

        self.assertFalse(project.open_to_candidates)

    def test_update_avg_score(self):
        user = user_model.objects.create(username='testuser', email='<EMAIL>', password='<PASSWORD>')
        project = Project.objects.create(name='Test Project', description='A test project', owner=user)

        self.assertEqual(project.score, 0)

        ProjectRating.objects.create(project=project, rated_by=user, score=4)
        ProjectRating.objects.create(project=project, rated_by=user, score=5)
        ProjectRating.objects.create(project=project, rated_by=user, score=3)

        project.update_avg_score()

        self.assertEqual(project.score, 4.0)

    def test_
