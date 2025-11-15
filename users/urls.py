from django.urls import path
from users import views
from projects import views as project_views
from django.contrib.auth import views as auth_views


app_name = 'users'

urlpatterns = [
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/register/', views.RegisterView.as_view(), name='register'),
    path('profile/<int:user_pk>/', views.DeveloperDetailView.as_view(), name='profile'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),
    path('profile/<int:user_pk>/update/', views.DeveloperUpdateView.as_view(), name='profile_update'),
    path('my-projects/', views.MyProjectListView.as_view(), name='my_projects'),
    path('my-tasks/', views.MyTasksListView.as_view(), name='my_tasks'),
    path('my-tasks/<int:task_pk>/', project_views.TaskDetailView.as_view(), name='my_tasks_detail'),
]