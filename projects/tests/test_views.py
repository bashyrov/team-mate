from django.contrib.auth import get_user_model
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse

from projects.models import Project, Task, Tag, ProjectOpenRole, ProjectApplication
from projects.views import ProjectListView

PROJECT_URL = reverse('projects:project_list')
user_model = get_user_model()

class PublicAccessTests(TestCase):

    def setUp(self):
        self.user = user_model.objects.create_user(
            username='testuser',
            email='test@mail.com',
            password='pass'
        )

        Project.objects.create(
            name='Test Project 1',
            description='A test project 1',
            owner=self.user
        )

        Tag.objects.create(
            name='Test Tag ',
        )

        ProjectOpenRole.objects.create(
            project=Project.objects.first(),
            role_name='Backend Developer',
        )

        Task.objects.create(
            title='Test Task',
            project=Project.objects.first(),
            assignee=get_user_model().objects.first(),
        )

        ProjectApplication.objects.create(
            project=Project.objects.first(),
            user=get_user_model().objects.first(),
            role=ProjectOpenRole.objects.first(),
        )

    LINKS = {
        'project_list': 200,
        'project_detail': 200,
        'project_create': 302,
        'project_edit': 302,
        'task_create': 302,
        'task_edit': 302,
        'project_rate': 302,
        'project_edit_roles': 302,
        'project_edit_stage': 302,
        'project_open_roles_list': 200,
        'project_open_roles_create': 302,
        'project_open_roles_delete': 302,
        'apply': 302,
        'applications_list': 302,
        'application_archive': 302,
        'application_approve': 302,
        'application_reject': 302,
        'task_list': 200,
    }


    def test_retrieve_projects_crud_public(self):
        project = Project.objects.first()
        project_pk = project.pk
        task_pk = Task.objects.first().pk
        role_pk = ProjectOpenRole.objects.first().pk
        application_pk = ProjectApplication.objects.first().pk

        ARGS = {
            'project_list': [],
            'project_detail': [
                {
                    'project_pk': project_pk,
                }
            ],
            'project_create': [],
            'project_edit': [
                {
                    'project_pk': project_pk,
                }
            ],
            'task_create': [
                {
                    'project_pk': project_pk,
                }
            ],
            'task_edit': [
                {
                    'project_pk': project_pk,
                    'task_pk': Task.objects.all().first().pk,
                }
            ],
            'project_rate': [
                {
                    'project_pk': project_pk,
                }
            ],
            'project_edit_roles': [
                {
                    'project_pk': project_pk,
                }
            ],
            'project_edit_stage': [
                {
                    'project_pk': project_pk,
                }
            ],
            'project_open_roles_list': [
                {
                    'project_pk': project_pk,
                }
            ],
            'project_open_roles_create': [
                {
                    'project_pk': project_pk,
                }
            ],
            'project_open_roles_delete': [
                {
                    'project_pk': project_pk,
                    'role_pk': ProjectOpenRole.objects.all().first().pk,
                }
            ],
            'apply': [
                {
                    'project_pk': project_pk,
                    'role_pk': ProjectOpenRole.objects.all().first().pk,
                }
            ],
            'applications_list': [
                {
                    'project_pk': project_pk,
                }
            ],
            'application_archive': [
                {
                    'project_pk': project_pk,
                }
            ],
            'application_approve': [
                {
                    'project_pk': project_pk,
                    'application_pk': ProjectApplication.objects.all().first().pk,
                }
            ],
            'application_reject': [
                {
                    'project_pk': project_pk,
                    'application_pk': ProjectApplication.objects.all().first().pk,
                }
            ],
            'task_list': [
                {
                    'project_pk': project_pk,
                }
            ]
        }

        for link, status_code in self.LINKS.items():
            args_list = ARGS.get(link, [{}])
            for args in args_list:
                url = reverse(f"projects:{link}", kwargs=args)
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code,
                    status_code,
                    f"Failed at {url} ({link}) with args {args}, expected {status_code} but got {response.status_code}"
                )


class ProjectTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = user_model.objects.create_user(
            username='testuser',
            email='test@mail.com',
            password='pass'
        )

        Project.objects.create(
            name='Test Project 1',
            description='A test project 1',
            owner=self.user
        )

        Project.objects.create(
            name='Test Project 2',
            description='A test project 2',
            owner=self.user
        )


class PrivateProjectTest(ProjectTests):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_retrieve_projects(self):
        response = self.client.get(PROJECT_URL)
        self.assertEqual(response.status_code, 200)

        projects = Project.objects.all()
        self.assertEqual(set(response.context['projects']), set(projects))

        self.assertTemplateUsed(response, 'projects/project_list.html')


class PrivateProjectCreateTests(ProjectTests):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        self.create_url = reverse('projects:project_create')

    def test_create_project_invalid_data(self):
        data = {'name': ''}
        response = self.client.post(self.create_url, data)
        self.assertEqual(response.status_code, 200)

    def test_retrieve_projects_public(self):
        response = self.client.post(self.create_url)
        self.assertEqual(response.status_code, 200)

class PrivateProjectUpdateTests(ProjectTests):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)
        self.project = Project.objects.first()
        self.update_url = reverse('projects:project_edit', kwargs={'project_pk': self.project.pk})

    def test_update_project_valid_data(self):
        data = {
            'name': 'Updated Project Name',
            'description': 'Updated description',
            'domain': 'technology',
            'development_stage': 'planning',
            'deploy_url': 'http://example.com',
            'project_url': 'http://project.com',
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 302)

        self.project.refresh_from_db()
        self.assertEqual(self.project.name, data['name'])
        self.assertEqual(self.project.description, data['description'])
        self.assertEqual(self.project.domain, data['domain'])
        self.assertEqual(self.project.development_stage, data['development_stage'])
        self.assertEqual(self.project.deploy_url, data['deploy_url'])
        self.assertEqual(self.project.project_url, data['project_url'])

    def test_update_project_invalid_data(self):
        data = {
            'name': '',
            'description': 'Updated description',
            'domain': 'technology',
            'development_stage': 'planning',
            'deploy_url': 'http://example.com',
            'project_url': 'http://project.com',
        }
        response = self.client.post(self.update_url, data)
        self.assertEqual(response.status_code, 200)

        self.project.refresh_from_db()
        self.assertNotEqual(self.project.name, data['name'])

    def test_update_project_stage_without_url(self):
        data = {
            'development_stage': 'deployed',
        }
        self.client.post(self.update_url, data)

        self.project.refresh_from_db()
        self.assertNotEqual(self.project.development_stage, data['development_stage'])

    def test_update_project_stage_with_url(self):
        data = {
            'development_stage': 'deployed',
            'deploy_url': 'http://example.com',
        }
        self.client.post(self.update_url, data)

        self.project.refresh_from_db()
        self.assertNotEqual(self.project.development_stage, data['development_stage'])


class ProjectListViewQuerysetTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = user_model.objects.create_user(username='testuser', password='pass')

        self.project1 = Project.objects.create(
            name="Alpha Project",
            owner=self.user,
            development_stage='initiation',
            domain='technology',
        )
        self.project2 = Project.objects.create(
            name="Beta Project",
            owner=self.user,
            development_stage='planning',
            domain='marketing',
        )
        self.project3 = Project.objects.create(
            name="Gamma Project",
            owner=self.user,
            development_stage='design',
            domain='technology',
        )
        ProjectOpenRole.objects.create(
            project=self.project1,
            role_name='Backend Developer'
        )

    def test_queryset_no_filters(self):
        request = self.factory.get('/projects/')
        request.user = self.user

        view = ProjectListView()
        view.request = request

        qs = view.get_queryset()
        self.assertEqual(set(qs), {self.project1, self.project2, self.project3})

    def test_queryset_filter_by_name(self):
        request = self.factory.get('/projects/', {'project_name': 'Alpha'})
        request.user = self.user

        view = ProjectListView()
        view.request = request

        qs = view.get_queryset()
        self.assertIn(self.project1, qs)
        self.assertNotIn(self.project2, qs)
        self.assertNotIn(self.project3, qs)

    def test_queryset_filter_by_development_stage(self):
        request = self.factory.get('/projects/', {'development_stage': 'planning'})
        request.user = self.user

        view = ProjectListView()
        view.request = request

        qs = view.get_queryset()
        self.assertEqual(list(qs), [self.project2])

    def test_queryset_filter_by_domain(self):
        request = self.factory.get('/projects/', {'domain': 'technology'})
        request.user = self.user

        view = ProjectListView()
        view.request = request

        qs = view.get_queryset()
        self.assertIn(self.project1, qs)
        self.assertIn(self.project3, qs)
        self.assertNotIn(self.project2, qs)

    def test_queryset_filter_open_to_candidates(self):
        request = self.factory.get('/projects/', {'open_to_candidates': 'on'})
        request.user = self.user

        view = ProjectListView()
        view.request = request

        qs = view.get_queryset()
        self.assertIn(self.project1, qs)
        self.assertNotIn(self.project3, qs)
        self.assertNotIn(self.project2, qs)

    def test_queryset_combined_filters(self):
        request = self.factory.get('/projects/', {
            'project_name': 'Gamma',
            'domain': 'technology',
            'open_to_candidates': 'on'
        })
        request.user = self.user

        view = ProjectListView()
        view.request = request

        qs = view.get_queryset()
        self.assertEqual(list(qs), [])