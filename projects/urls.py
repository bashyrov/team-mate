from django.urls import path
from projects import views


app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='dashboard'),
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/<int:project_pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('projects/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:project_pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('projects/<int:project_pk>/rate/', views.ProjectRatingCreateView.as_view(), name='project_rate'),
    path('projects/<int:project_pk>/roles/edit/', views.ProjectRolesUpdateView.as_view(), name='project_edit_roles'),
    path('projects/<int:project_pk>/stage/edit/', views.ProjectStageUpdateView.as_view(), name='project_edit_stage'),
    path('projects/<int:project_pk>/open-roles/', views.ProjectOpenRoleListView.as_view(), name='project_open_roles_list'),
    path('projects/<int:project_pk>/open-roles/create/', views.ProjectOpenRoleCreateView.as_view(), name='project_open_roles_create'),
    path('projects/<int:project_pk>/open-roles/<int:role_pk>/delete', views.ProjectOpenRoleDeleteView.as_view(), name='project_open_roles_delete'),
    path("projects/<int:project_pk>/open-roles/<int:role_pk>/apply/", views.ProjectApplicationCreateView.as_view(), name="apply"),
    path("projects/<int:project_pk>/applications/", views.ProjectApplicationListView.as_view(view_type='active'), name="applications_list"),
    path('projects/<int:project_pk>/applications/archive/', views.ProjectApplicationListView.as_view(view_type='archive'), name='application_archive'),
    path('projects/<int:project_pk>/applications/<int:application_pk>/approve/', views.application_approve, name='application_approve'),
    path('projects/<int:project_pk>/applications/<int:application_pk>/reject/', views.application_reject, name='application_reject'),
    path('projects/<int:project_pk>/tasks/', views.TaskListView.as_view(), name='task_list'),
    path('projects/<int:project_pk>/tasks/create/', views.TaskCreateView.as_view(), name='task_create'),
    path("projects/<int:project_pk>/tasks/<int:task_pk>/edit/", views.TaskUpdateView.as_view(), name="task_edit"),
    path("projects/<int:project_pk>/tasks/<int:task_pk>/", views.TaskDetailView.as_view(), name="task_detail"),
]