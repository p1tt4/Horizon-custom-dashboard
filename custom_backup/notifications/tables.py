import logging

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables, exceptions
from openstack_dashboard.dashboards.custom_backup.db_api import delete_notification


logger = logging.getLogger(__name__)


class CreateNotification(tables.LinkAction):
    name = "create"
    verbose_name = _("Create New Notification")
    url = "horizon:custom_backup:notifications:create"
    classes = ("ajax-modal",)
    icon = "plus"


class UpdateNotification(tables.LinkAction):
    name = "update"
    verbose_name = _("Update Notification")
    url = "horizon:custom_backup:notifications:update"
    classes = ("ajax-modal",)
    icon = "pencil"


class DeleteNotification(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Notification",
            u"Delete Notifications",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Delete Notification",
            u"Delete Notifications",
            count
        )

    def delete(self, request, notification_id):
        try:
            delete_notification(notification_id)
        except (exceptions.HandledException, exceptions.NotFound) as e:
            logger.error("Failed to delete Notification with ID {}: {}".format(notification_id, e))


class TriggerIdColumn(tables.Column):
    def get_link_url(self, datum):
        trigger_url = "horizon:custom_backup:notifications:detail"
        return reverse(trigger_url, args=[datum.id])


class NotificationsTable(tables.DataTable):

    id = TriggerIdColumn(
        "id",
        verbose_name=_("ID"),
        link=True
    )
    backup_name = tables.Column(
        "name",
        verbose_name=_("Notification Name")
    )
    sender_address = tables.Column(
        "sender_address",
        verbose_name=_("Sender address"),
    )
    recipient_address = tables.Column(
        "recipient_address",
        verbose_name=_("Recipient address"),
    )
    smtp_server = tables.Column(
        "smtp_server",
        verbose_name=_('SMTP Server'),
    )
    openstack_url = tables.Column(
        "openstack_url",
        verbose_name=_("Openstack Url"),
    )
    creation_time = tables.Column(
        "creation_time",
        verbose_name=_("Creation Time"),
    )
    update_time = tables.Column(
        "update_time",
        verbose_name=_("Modification Time"),
    )

    def get_object_id(self, datum):
        return datum.id

    class Meta(object):
        name = "notifications"
        verbose_name = _("Notifications")
        table_actions = (
            tables.FilterAction,
            CreateNotification,
            DeleteNotification
        )
        row_actions = (UpdateNotification, DeleteNotification)
