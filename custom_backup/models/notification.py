from uuid import uuid1
from django.db import models
from openstack_dashboard.dashboards.custom_backup.constants import constants


class Notification(models.Model):
    id = models.CharField(max_length=constants.UUID_MAX_LEN, primary_key=True)
    name = models.CharField(max_length=constants.STRING_L)
    sender_address = models.EmailField(max_length=constants.STRING_L)
    recipient_address = models.EmailField(max_length=constants.STRING_L)
    smtp_server = models.GenericIPAddressField(null=True)
    openstack_url = models.URLField()
    creation_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(null=True)

    class Meta:
        unique_together = (('name', 'sender_address', 'recipient_address'), )

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if not self.id:
            self.id = str(uuid1())
        super(Notification, self).save(force_insert=False, force_update=False, using=None, update_fields=None)

    def __str__(self):
        return "Notification: {} - {} - {}".format(self.name, self.sender_address, self.recipient_address)
