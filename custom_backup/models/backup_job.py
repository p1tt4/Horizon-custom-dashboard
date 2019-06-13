from uuid import uuid1
from django.db import models
from openstack_dashboard.dashboards.custom_backup.constants import constants


class BackupJob(models.Model):
    id = models.CharField(max_length=constants.UUID_MAX_LEN, primary_key=True)
    name = models.CharField(max_length=constants.STRING_L, unique=True)
    schedule_pattern = models.CharField(max_length=constants.STRING_M)
    workflow_input = models.TextField()
    creation_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(null=True)
    cron_trigger_id = models.CharField(max_length=constants.UUID_MAX_LEN)
    enabled = models.BooleanField(default=True)
    project_id = models.CharField(max_length=constants.PROJECT_ID_LEN)
    notification = models.ForeignKey("Notification", null=True)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.id:
            self.id = str(uuid1())
        super(BackupJob, self).save(force_insert=False, force_update=False, using=None, update_fields=None)

    def __str__(self):
        return "BackupJob with id and name: {} : {}".format(self.id, self.name)
