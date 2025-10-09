from django.contrib import admin
from .models import Developer, DeveloperRatings

@admin.register(Developer)
class DeveloperAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'email', 'position', 'score', 'tech_stack', 'linkedin_url', 'portfolio_url'
    )
    list_filter = ('position',)
    search_fields = ('username', 'email', 'tech_stack', 'linkedin_url', 'portfolio_url')


@admin.register(DeveloperRatings)
class DeveloperRatingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_added', 'project', 'rating', 'created_at')
    list_filter = ('rating', 'project')
    search_fields = ('user__username', 'user_added__username', 'project__name')
