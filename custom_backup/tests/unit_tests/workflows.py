import os
from uuid import uuid1
from django.contrib.auth.models import User
from django.test import RequestFactory

from mock import patch, MagicMock
from django.core.urlresolvers import reverse
from openstack_dashboard.test.helpers import TestCase

from openstack_dashboard.dashboards.custom_backup.jobs.workflows import NameAction, CreateBackupJobWorkflow
from openstack_dashboard.dashboards.custom_backup.tests import MockNotificationObject, MockNovaServerElement, \
    MockTriggerObject


class BackupWorkflowValidationTestCase(TestCase):

    def setUp(self):
        super(BackupWorkflowValidationTestCase, self).setUp()
        self.fake_nova_server = MockNovaServerElement()
        self.patched_api_method = patch(
            'openstack_dashboard.dashboards.custom_backup.jobs.workflows.nova_server_list',
            return_value=([self.fake_nova_server], False)
        )
        self.patched_api_method.start()
        self.url = 'horizon:custom_backup:jobs:create'
        self.tenant_id = '10'

    def tearDown(self):
        self.patched_api_method.stop()

    def init_workflow(self, payload):
        rf = RequestFactory()
        post_request = rf.post(reverse(self.url), data=payload)
        # Remind to use the spec parameter, not the spec_set when initializing the MagickMock otherwise it won't be
        # possible to set the tenant_id attribute, which is not strictly inherent of the Django User model
        post_request.user = MagicMock(spec=User)
        post_request.user.tenant_id = self.tenant_id
        return CreateBackupJobWorkflow(request=post_request), post_request

    def test_backup_job_create_empty_payload(self):
        workflow_obj, _request = self.init_workflow(payload=dict())
        self.assertFalse(workflow_obj.is_valid())
        self.assertEqual(workflow_obj.steps[0].action.errors['error_field'], ['Name field is required'])

    def test_name_step_missing_source(self):
        workflow_obj, _request = self.init_workflow({'name': 'backup'})
        self.assertFalse(workflow_obj.is_valid())
        self.assertEqual(
            workflow_obj.steps[0].action.errors['error_field'],
            ['Source field is required. Provide a metadata key-value pair or select one instance']
        )

    def test_name_step_both_source_parameters_are_filled(self):
        payload = {'name': 'backup', 'instance': self.fake_nova_server.id, 'metadata_value': 'value', 'metadata_key': 'key'}
        workflow_obj, _request = self.init_workflow(payload)
        self.assertFalse(workflow_obj.is_valid())
        self.assertEqual(
            workflow_obj.steps[0].action.errors['error_field'],
            ['Only one source input can be provided, either Metadata or Instance']
        )

    def test_name_step_misc_filling(self):
        payload = {'name': 'backup', 'instance': self.fake_nova_server.id, 'metadata_key': 'key'}
        workflow_obj, _request = self.init_workflow(payload)
        self.assertFalse(workflow_obj.is_valid())
        self.assertEqual(
            workflow_obj.steps[0].action.errors['error_field'],
            ['Ensure you filled both metadata key and value']
        )

    def test_name_step_is_valid(self):
        """
        Being that the only required field are name and source, belonging to the name-step, if they provided and are
        valid, the whole workflow is valid
        """
        payload = {'name': 'backup', 'instance': self.fake_nova_server.id}
        workflow_obj, _request = self.init_workflow(payload)
        self.assertTrue(workflow_obj.is_valid())
        self.assertEqual(workflow_obj.steps[0].action.errors, {})

    @patch('openstack_dashboard.dashboards.custom_backup.jobs.workflows.create_backup_job')
    def test_backup_creation_workflow(self, create_backup_job):
        payload = {
            'name': 'backup',
            'instance': self.fake_nova_server.id,
            'stop_instance': False,
            'pause_instance': True,
            'backup_mode': True,
            'preserve_snapshot': False,
            'max_backups': 2,
            'max_snapshots': 2,
            'backup_type': 'auto',
            'minute': '*',
            'hour': '*',
            'day': '*',
            'month': '*',
            'weekday': '*'
        }
        workflow_obj, _request = self.init_workflow(payload)
        workflow_obj.finalize()
        create_backup_job.assert_called_with(
            request=_request,
            name='backup',
            workflow_input={
                'instance_pause': True,
                'instance_stop': False,
                'pattern': "{0}_backup_{1}",
                'instance': self.fake_nova_server.id,
                'only_os': False,
                'cinder_backup': True,
                'max_snapshots': 2,
                'max_backups': 2,
                'only_backup': True,
                'backup_type': 'auto',
                'metadata': None,
            },
            schedule_pattern='* * * * *',
            tenant_id=self.tenant_id,
            notification=None
        )

    @patch('openstack_dashboard.dashboards.custom_backup.jobs.workflows.create_backup_job')
    def test_backup_creation_workflow_with_metadata(self, create_backup_job):
        payload = {
            'name': 'backup',
            'metadata_key': 'key',
            'metadata_value': 'value',
            'stop_instance': False,
            'pause_instance': True,
            'backup_mode': True,
            'preserve_snapshot': False,
            'max_backups': 2,
            'max_snapshots': 2,
            'backup_type': 'auto',
            'minute': '*',
            'hour': '*',
            'day': '*',
            'month': '*',
            'weekday': '*'
        }
        workflow_obj, _request = self.init_workflow(payload)
        workflow_obj.finalize()
        create_backup_job.assert_called_with(
            request=_request,
            name='backup',
            workflow_input={
                'instance_pause': True,
                'instance_stop': False,
                'pattern': "{0}_backup_{1}",
                'instance': None,
                'only_os': False,
                'cinder_backup': True,
                'max_snapshots': 2,
                'max_backups': 2,
                'only_backup': True,
                'backup_type': 'auto',
                'metadata': {'key': 'key', 'value': 'value'},
            },
            schedule_pattern='* * * * *',
            tenant_id=self.tenant_id,
            notification=None
        )

    @patch('openstack_dashboard.dashboards.custom_backup.jobs.workflows.list_notifications')
    def test_workflow_notification_valid_id(self, list_notifications):
        notification_obj = MockNotificationObject()
        list_notifications.return_value = [notification_obj, ]
        payload = {'name': 'backup', 'instance': self.fake_nova_server.id, 'notification': notification_obj.id}
        workflow_obj, _request = self.init_workflow(payload)
        self.assertTrue(workflow_obj.is_valid())

    @patch('openstack_dashboard.dashboards.custom_backup.jobs.workflows.list_notifications')
    def test_workflow_notification_invalid_id(self, list_notifications):
        list_notifications.return_value = [MockNotificationObject(), ]
        payload = {'name': 'backup', 'instance': self.fake_nova_server.id, 'notification': 10}
        workflow_obj, _request = self.init_workflow(payload)
        self.assertFalse(workflow_obj.is_valid())

    @patch('openstack_dashboard.dashboards.custom_backup.jobs.workflows.create_backup_job')
    @patch('openstack_dashboard.dashboards.custom_backup.jobs.workflows.list_notifications', return_value=[])
    def test_workflow_creation_with_minimal_payload(self, list_notifications, create_backup_job):
        """
        verify that the default values are those expected
        """
        payload = {'name': 'backup', 'instance': self.fake_nova_server.id, }
        workflow_obj, _request = self.init_workflow(payload)
        workflow_obj.finalize()
        create_backup_job.assert_called_with(
            request=_request,
            name='backup',
            workflow_input={
                'instance_pause': False,
                'instance_stop': False,
                'pattern': "{0}_backup_{1}",
                'instance': self.fake_nova_server.id,
                'only_os': False,
                'cinder_backup': False,
                'max_snapshots': None,
                'max_backups': None,
                'only_backup': True,
                'backup_type': '',
                'metadata': None,
            },
            schedule_pattern='* * * * *',
            tenant_id=self.tenant_id,
            notification=None
        )

    @patch('openstack_dashboard.dashboards.custom_backup.jobs.workflows.create_backup_job')
    @patch('openstack_dashboard.dashboards.custom_backup.jobs.workflows.list_notifications', return_value=[])
    def test_workflow_creation_without_mandatory_data(self, list_notifications, create_backup_job):
        """
        Because the finalize method is executed also when a step is not valid (given that all the required
        arguments are provided) leading to potential unexpected problems, I fixed this behavior by enforcing that
        all steps must be valid.
        This test checks that this enforcement works
        """
        payload = {'name': 'backup'}
        workflow_obj, _request = self.init_workflow(payload)
        self.assertFalse(workflow_obj.is_valid())
        workflow_obj.finalize()
        create_backup_job.assert_not_called()


