from django.contrib.auth import get_user_model
from django.test import TestCase

from projects.models import (Project,
                             ProjectMembership,
                             ProjectOpenRole,
                             ProjectRating,
                             Tag,
                             Task)

user_model = get_user_model()


class ModelsTestCase(TestCase):

    def setUp(self):
        self.user = user_model.objects.create(
            username='testuser',
            email='test@mail.com',
            password='pass'
        )

    def test_project_str(self):

        project = Project.objects.create(
            name='Test Project',
            description='A test project',
            owner=self.user
        )

        self.assertEqual(str(project), project.name)

    def test_get_members(self):

        user_1 = user_model.objects.create(
            username='testuser1',
            email='<EMAIL>',
            password='<PASSWORD>'
        )
        user_2 = user_model.objects.create(
            username='testuser2',
            email='<EMAIL>',
            password='<PASSWORD>'
        )
        user_3 = user_model.objects.create(
            username='testuser3',
            email='<EMAIL>',
            password='<PASSWORD>'
        )
        user_4 = user_model.objects.create(
            username='testuser4',
            email='<EMAIL>',
            password='<PASSWORD>'
        )

        project = Project.objects.create(
            name='Test Project',
            description='A test project',
            owner=user_1
        )

        ProjectMembership.objects.create(
            project=project,
            user=user_2,
            role='DEV'
        )
        ProjectMembership.objects.create(
            project=project,
            user=user_3,
            role='LEAD'
        )
        ProjectMembership.objects.create(
            project=project,
            user=user_4,
            role='PM'
        )

        members = project.get_members()
        expected_members = user_model.objects.filter(
            pk__in=[
                user_1.pk, user_2.pk, user_3.pk, user_4.pk
            ]
        )

        self.assertSetEqual(set(members), set(expected_members))

    def test_open_to_candidates(self):

        project = Project.objects.create(
            name='Test Project',
            description='A test project',
            owner=self.user
        )

        self.assertFalse(project.open_to_candidates)

        ProjectOpenRole.objects.create(project=project)

        project = Project.objects.get(pk=project.pk)
        self.assertTrue(project.open_to_candidates)

        ProjectOpenRole.objects.filter(project=project).first().delete()

        project = Project.objects.get(pk=project.pk)
        self.assertFalse(project.open_to_candidates)

    def test_update_avg_score(self):

        project = Project.objects.create(
            name='Test Project',
            description='A test project',
            owner=self.user
        )

        self.rater1 = user_model.objects.create(
            username='rater1',
            password='<PASSWORD>'
        )
        self.rater2 = user_model.objects.create(
            username='rater2',
            password='<PASSWORD>'
        )

        self.assertEqual(project.score, 0)

        ProjectRating.objects.create(
            project=project,
            rated_by=self.user,
            score=4
        )
        ProjectRating.objects.create(
            project=project,
            rated_by=self.rater1,
            score=5
        )
        ProjectRating.objects.create(
            project=project,
            rated_by=self.rater2,
            score=3
        )

        project.update_avg_score()

        self.assertEqual(project.score, 4.0)

    def test_has_permission(self):

        user_test = user_model.objects.create(
            username='dev',
            email='dev@mail.com',
            password='pass'
        )
        project = Project.objects.create(
            name='Test Project',
            owner=self.user
        )

        membership = ProjectMembership.objects.create(
            project=project,
            user=user_test,
            role='DEV',
            edit_project_info_perm=True,
            update_project_stage_perm=True,
        )

        admin_perms = ['edit_project_info_perm', 'add_task_perm', 'update_project_stage_perm', 'manage_open_roles_perm']
        admin_membership = ProjectMembership.objects.get(project=project, user=self.user)

        for perm in admin_perms:
            self.assertTrue(admin_membership.has_permission(perm))

        perms_expectations = {
            'edit_project_info_perm': True,
            'add_task_perm': False,
            'update_project_stage_perm': True,
            'manage_open_roles_perm': False,
        }

        for perm, expected in perms_expectations.items():
            self.assertEqual(membership.has_permission(perm), expected)

    def test_projectmembership_str(self):

        project = Project.objects.create(
            name='Test Project',
            owner=self.user
        )

        membership_obj = ProjectMembership.objects.all().filter(
            project=project,
            user=self.user
        ).first()

        self.assertEqual(str(membership_obj),
                         f"{membership_obj.user.username} in "
                         f"{membership_obj.project.name} as "
                         f"{membership_obj.get_role_display()}")

    def test_tag_str(self):
        tag = Tag.objects.create(name='Django')

        self.assertEqual(str(tag), tag.name)

    def test_task_str(self):

        project = Project.objects.create(
            name='Test Project',
            owner=self.user
        )
        task = Task.objects.create(
            title='Test Task',
            description='A test task',
            project=project,
            created_by=self.user
        )

        self.assertEqual(str(task), task.title)

    def test_project_open_role_str(self):

        project = Project.objects.create(
            name='Test Project',
            owner=self.user
        )

        role = ProjectOpenRole.objects.create(
            project=project,
            role_name='DEV'
        )

        self.assertEqual(str(role), f"{project.name} - {role.role_name}")