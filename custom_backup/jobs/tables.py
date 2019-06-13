import logging
from json import loads as json_loads

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables, exceptions
from openstack_dashboard.dashboards.custom_backup.db_api import delete_backup_job


logger = logging.getLogger(__name__)


class CreateBackupJob(tables.LinkAction):
    name = "create"
    verbose_name = _("Create New BackupJob")
    url = "horizon:custom_backup:jobs:create"
    classes = ("ajax-modal",)
    icon = "plus"


class UpdateBackupJob(tables.LinkAction):
    name = "update"
    verbose_name = _("Update BackupJob")
    url = "horizon:custom_backup:jobs:update"
    classes = ("ajax-modal",)
    icon = "pencil"


class CloneBackupJob(tables.LinkAction):
    name = "clone"
    verbose_name = _("Clone BackupJob")
    url = "horizon:custom_backup:jobs:clone"
    classes = ("ajax-modal",)
    icon = "pencil"


class DeleteBackupJob(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete BackupJob",
            u"Delete BackupJobs",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Delete BackupJob",
            u"Delete BackupJobs",
            count
        )

    def delete(self, request, backup_job_id):
        if not delete_backup_job(request, backup_job_id):
            logger.error("Failed to delete BackupJob {}".format(backup_job_id))


# todo: NOT USED: REMOVE ?
def tags_to_string(workflow):
    return ', '.join(workflow.tags) if workflow.tags else None


def cut(workflow, length=50):
    inputs = workflow.input

    if inputs and len(inputs) > length:
        return "%s..." % inputs[:length], True
    else:
        return inputs, False


class TriggerIdColumn(tables.Column):
    def get_link_url(self, datum):
        trigger_url = "horizon:custom_backup:jobs:detail"
        return reverse(trigger_url, args=[datum.id])


class JobsTable(tables.DataTable):

    def _workflow_input(datum):
        # this callable converts the json string to a string of type key1=value1, key2=value2, ...
        raw_data = getattr(datum, 'workflow_input', '')
        return ", ".join(["{}={}".format(k,v) for k, v in json_loads(raw_data).items()])

    id = TriggerIdColumn(
        "id",
        verbose_name=_("ID"),
        link=True
    )
    backup_name = tables.Column(
        "name",
        verbose_name=_("Backup Name")
    )
    workflow_input = tables.Column(
        _workflow_input,
        verbose_name=_("Workflow Input"),
    )
    schedule_pattern = tables.Column(
        "schedule_pattern",
        verbose_name=_("Schedule Pattern"),
    )
    cron_trigger_id = tables.Column(
        "cron_trigger_id",
        verbose_name=_('Cron Trigger Id'),
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
        name = "jobs"
        verbose_name = _("Jobs")
        table_actions = (
            tables.FilterAction,
            CreateBackupJob,
            DeleteBackupJob
        )
        row_actions = (UpdateBackupJob, CloneBackupJob, DeleteBackupJob)
