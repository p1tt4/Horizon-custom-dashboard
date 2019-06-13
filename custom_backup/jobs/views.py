import logging
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views import generic
from horizon import exceptions, workflows, tables
import tables as backup_tables
import workflows as backup_workflows
from openstack_dashboard.dashboards.custom_backup.constants import constants
from openstack_dashboard.dashboards.custom_backup.db_api import all_backup_jobs, get_backup_job


logger = logging.getLogger(__name__)


class BackupJobException(exceptions.HandledException):
    """"""


class IndexView(tables.DataTableView):
    table_class = backup_tables.JobsTable
    template_name = 'custom_backup/jobs/index.html'

    def get_data(self):
        return all_backup_jobs(as_list=True)


class CreateView(workflows.WorkflowView):
    workflow_class = backup_workflows.CreateBackupJobWorkflow


class UpdateView(workflows.WorkflowView):
    workflow_class = backup_workflows.UpdateBackupJob


class CloneView(workflows.WorkflowView):
    workflow_class = backup_workflows.CloneBackupJob


class DetailView(generic.TemplateView):
    template_name = 'custom_backup/jobs/detail.html'
    page_title = _("BackupJob Details")

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        backup_job = get_backup_job(id=kwargs['backup_job_id'])
        context['backup_job'] = backup_job
        context['list_url'] = reverse_lazy('horizon:custom_backup:jobs:index')
        cron_trigger_name = constants.NAME_PREFIX.format(backup_job.name)
        context['cron_trigger_name'] = cron_trigger_name
        context['cron_trigger_details_url'] = reverse('horizon:mistral:cron_triggers:detail', args=[cron_trigger_name])
        context["custom_breadcrumb"] = ''
        return context
