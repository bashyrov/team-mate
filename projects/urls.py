from django.urls import path
from projects import views


app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='dashboard'),
    path('profile/<int:user_pk>/', views.DeveloperDetailView.as_view(), name='profile'),
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('my-projects/', views.MyProjectListView.as_view(), name='my_projects'),
    path('project/<int:project_pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('project/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('project/<int:project_pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('project/<int:project_pk>/applicate/', views.ProjectUpdateView.as_view(), name='project_applicate'),
    path('project/rating/<int:project_pk>/', views.ProjectRatingCreateView.as_view(), name='project_rate'),
    path('project/<int:project_pk>/roles/edit/', views.ProjectRolesUpdateView.as_view(), name='project_edit_roles'),
    path('project/<int:project_pk>/stage/edit/', views.ProjectStageUpdateView.as_view(), name='project_edit_stage'),
    path('project/<int:project_pk>/task/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('project/<int:project_pk>/open-roles', views.ProjectOpenRoleListView.as_view(), name='project_open_roles_list'),
    path('project/<int:project_pk>/open-roles/create/', views.ProjectOpenRoleCreateView.as_view(), name='project_open_roles_create'),
    path('project/<int:project_pk>/open-roles/<int:role_pk>/delete', views.ProjectOpenRoleDeleteView.as_view(), name='project_open_roles_delete'),
    path("projects/<int:project_pk>/apply/", views.ProjectApplicationCreateView.as_view(), name="apply"),
    path("projects/<int:project_pk>/tasks/<int:task_pk>/edit/", views.TaskUpdateView.as_view(), name="task_edit"),
    path("projects/<int:project_pk>/tasks/<int:task_pk>/", views.TaskDetailView.as_view(), name="task_detail"),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),
]