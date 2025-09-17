from django.urls import path
from projects import views


app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='dashboard'),
    path('projects/', views.ProjectListView.as_view(), name='project-list'),
    path('my-projects/', views.MyProjectListView.as_view(), name='my_projects'),
    path('project/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('project/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('project/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),

    path('profile/<int:pk>/', views.DeveloperDetailView.as_view(), name='profile'),

    path('project/<int:project_pk>/task/create/', views.TaskCreateView.as_view(), name='task_create'),
    path('task/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task_edit'),
]