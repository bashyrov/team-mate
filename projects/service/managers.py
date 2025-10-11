from team_mate import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg


class ProjectManager(models.Manager):

    def validate_stage(self, project):
        if project.development_stage == 'deployed' and not project.deploy_url:
            raise ValidationError({
                'stage': 'Cannot set stage to "Deployed" without a deploy URL.'
            })
        return True