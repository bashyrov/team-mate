from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('my-projects/', views.my_projects, name='my_projects'),
    path('project/<int:pk>/', views.project_detail, name='project_detail'),
    path('profile/<int:pk>/', views.profile, name='profile'),

    # CRUD для проектов
    path('project/create/', views.project_create, name='project_create'),
    path('project/<int:pk>/edit/', views.project_edit, name='project_edit'),

    # CRUD для задач
    path('project/<int:project_pk>/task/create/', views.task_create, name='task_create'),
    path('task/<int:pk>/edit/', views.task_edit, name='task_edit'),
]
