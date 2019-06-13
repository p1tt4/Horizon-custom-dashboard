# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.views import generic
from horizon import workflows, tables
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from openstack_dashboard.dashboards.custom_backup.db_api import list_notifications, \
    get_notification, get_backup_jobs_of_notification
from openstack_dashboard.dashboards.custom_backup.notifications import workflows as notification_workflows
from openstack_dashboard.dashboards.custom_backup.notifications import tables as notification_table


class IndexView(tables.DataTableView):
    table_class = notification_table.NotificationsTable
    template_name = 'custom_backup/notifications/index.html'

    def get_data(self):
        return list_notifications(as_list=True)


class CreateView(workflows.WorkflowView):
    workflow_class = notification_workflows.CreateNotificationWorkflow


class UpdateView(workflows.WorkflowView):
    workflow_class = notification_workflows.UpdateNotificationWorkflow


class DetailView(generic.TemplateView):
    template_name = 'custom_backup/notifications/detail.html'
    page_title = _("Notification Details")

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        notification = get_notification(id=kwargs['notification_id'])
        context['notification'] = notification
        context['backup_jobs'] = get_backup_jobs_of_notification(notification.id)
        context['index_url'] = reverse_lazy('horizon:custom_backup:notifications:index')
        return context

