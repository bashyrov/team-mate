from django.contrib.auth import get_user_model
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse

from projects.models import ProjectMembership, Tag, ProjectOpenRole, Task, ProjectApplication, Project

class PermissionTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.user_model = get_user_model()

        self.user_owner = self.user_model.objects.create_user(
            username='owner',
            email='<EMAIL>',
            password='ownerpass'
        )
        self.only_task_perm_user = self.user_model.objects.create_user(
            username='only_task_perm_user',
            email='<EMAIL>',
            password='memberpass'
        )
        self.project_info_perm_user = self.user_model.objects.create_user(
            username='project_info_perm_user',
            email='<EMAIL>',
            password='memberpass'
        )
        self.update_project_stage_perm_user = self.user_model.objects.create_user(
            username='update_project_stage_perm_user',
            email='<EMAIL>',
            password='memberpass'
        )
        self.manage_open_roles_perm_user = self.user_model.objects.create_user(
            username='manage_open_roles_perm_user',
            email='<EMAIL>',
            password='memberpass'
        )
        self.non_member = self.user_model.objects.create_user(
            username='non_member',
            email='<EMAIL>',
            password='nonmemberpass'
        )
        self.assigned_to_task = self.user_model.objects.create_user(
            username='assigned_to_task',
            email='<EMAIL>',
            password='memberpass'
        )

        self.project = self.user_owner.projects.create(
            name='Test Project',
            description='A test project',
            owner=self.user_owner
        )
        ProjectMembership.objects.create(
            project=self.project,
            user=self.only_task_perm_user,
            role='DEV',
            add_task_perm=True,
        )
        ProjectMembership.objects.create(
            project=self.project,
            user=self.project_info_perm_user,
            role='DEV',
            edit_project_info_perm=True,
        )
        ProjectMembership.objects.create(
            project=self.project,
            user=self.update_project_stage_perm_user,
            role='DEV',
            update_project_stage_perm=True,
        )
        ProjectMembership.objects.create(
            project=self.project,
            user=self.manage_open_roles_perm_user,
            role='DEV',
            manage_open_roles_perm=True,
        )

        self.tag = Tag.objects.create(
            name='Test Tag ',
        )

        self.open_role = ProjectOpenRole.objects.create(
            project=self.project,
            role_name='Backend Developer',
        )

        self.task = Task.objects.create(
            title='Test Task',
            project=self.project,
            assignee=self.assigned_to_task,
        )

        self.application = ProjectApplication.objects.create(
            project=Project.objects.first(),
            user=self.non_member,
            role=ProjectOpenRole.objects.first(),
        )

    def test_owner_has_all_permissions(self):
        membership = ProjectMembership.objects.get(project=self.project, user=self.user_owner)
        perms = [
            'edit_project_info_perm',
            'add_task_perm',
            'update_project_stage_perm',
            'manage_open_roles_perm'
        ]
        for perm in perms:
            self.assertTrue(membership.has_permission(perm), f"Owner should have {perm}")

    def test_only_task_permission_user(self):
        membership = ProjectMembership.objects.get(project=self.project, user=self.only_task_perm_user)
        self.assertTrue(membership.has_permission('add_task_perm'))
        self.assertFalse(membership.has_permission('edit_project_info_perm'))
        self.assertFalse(membership.has_permission('update_project_stage_perm'))
        self.assertFalse(membership.has_permission('manage_open_roles_perm'))

    def test_project_info_permission_user(self):
        membership = ProjectMembership.objects.get(project=self.project, user=self.project_info_perm_user)
        self.assertTrue(membership.has_permission('edit_project_info_perm'))
        self.assertFalse(membership.has_permission('add_task_perm'))
        self.assertFalse(membership.has_permission('update_project_stage_perm'))
        self.assertFalse(membership.has_permission('manage_open_roles_perm'))

    def test_update_project_stage_permission_user(self):
        membership = ProjectMembership.objects.get(project=self.project, user=self.update_project_stage_perm_user)
        self.assertTrue(membership.has_permission('update_project_stage_perm'))
        self.assertFalse(membership.has_permission('edit_project_info_perm'))
        self.assertFalse(membership.has_permission('add_task_perm'))
        self.assertFalse(membership.has_permission('manage_open_roles_perm'))

    def test_manage_open_roles_permission_user(self):
        membership = ProjectMembership.objects.get(project=self.project, user=self.manage_open_roles_perm_user)
        self.assertTrue(membership.has_permission('manage_open_roles_perm'))
        self.assertFalse(membership.has_permission('edit_project_info_perm'))
        self.assertFalse(membership.has_permission('add_task_perm'))
        self.assertFalse(membership.has_permission('update_project_stage_perm'))

    def test_non_member_has_no_permissions(self):
        membership = ProjectMembership.objects.filter(project=self.project, user=self.non_member).first()
        self.assertIsNone(membership)
