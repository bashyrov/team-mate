from django.urls import path
from users import views


app_name = 'users'

urlpatterns = [
    path('profile/<int:user_pk>/', views.DeveloperDetailView.as_view(), name='profile'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),
]