from django.urls import path
from projects import views


app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='dashboard'),
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('my-projects/', views.MyProjectListView.as_view(), name='my_projects'),
    path('project/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('project/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('project/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('project/<int:pk>/applicate/', views.ProjectUpdateView.as_view(), name='project_applicate'),
    path('project/rating/<int:pk>/', views.ProjectRatingCreateView.as_view(), name='project_rate'),
    path('project/<int:pk>/roles/edit/', views.ProjectRolesUpdateView.as_view(), name='project_edit_roles'),
    path('project/<int:pk>/stage/edit/', views.ProjectStageUpdateView.as_view(), name='project_edit_stage'),
    path('profile/<int:pk>/', views.DeveloperDetailView.as_view(), name='profile'),
    path('project/<int:pk>/task/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('project/<int:pk>/open-roles', views.ProjectOpenRoleListView.as_view(), name='project_open_roles'),
    path('project/<int:pk>/open-roles/create/', views.ProjectOpenRoleCreateView.as_view(), name='project_open_roles_create'),
    path("projects/<int:pk>/apply/", views.ProjectApplicationCreateView.as_view(), name="apply"),
    path('task/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_edit'),
    path('task/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),
]