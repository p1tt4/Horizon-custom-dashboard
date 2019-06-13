from json import loads
from django.test import TestCase
from django.core.exceptions import MultipleObjectsReturned
from mock import patch, MagicMock
from mistralclient.api.base import APIException
from openstack_dashboard.dashboards.custom_backup.db_api import Notification
from openstack_dashboard.dashboards.custom_backup.db_api import create_cron_trigger, update_cron_trigger, \
    delete_cron_trigger, get_backup_jobs_of_notification, delete_backup_job, delete_notification


class FakeRequest(object):
    """"""


class FakeBackUpJob(object):
    name = 'test-trigger'
    workflow_input = '{"instance": "server"}'
    schedule_pattern = '* * * * *'
    called = False

    def delete(self):
        pass


class FakeNotification(object):
    backupjob_set = Notification


class TriggerMethodsTestCase(TestCase):

    def setUp(self):
        self.request = FakeRequest()
        self.default_cron_schedule = '* * * * *'
        self.backup_job_name = 'test-trigger'

    @patch('openstack_dashboard.dashboards.custom_backup.db_api.api.cron_trigger_create')
    def test_create_cron_trigger_case_1(self, mocked_method):
        expected_trigger_name = "Cron Trigger for Backup {}".format(self.backup_job_name)
        create_cron_trigger(self.request, self.backup_job_name, {}, self.default_cron_schedule)
        mocked_method.assert_called_with(
            self.request,
            expected_trigger_name,
            'custom_instance_backup.custom_instance_backup',
            {},
            '',
            self.default_cron_schedule,
            None,
            None
        )

    @patch('openstack_dashboard.dashboards.custom_backup.db_api.api.cron_trigger_delete')
    def test_delete_cron_trigger_case_1(self, mocked_method):
        delete_cron_trigger(self.request, self.backup_job_name)
        mocked_method.assert_called_with(self.request, "Cron Trigger for Backup {}".format(self.backup_job_name))

    @patch('openstack_dashboard.dashboards.custom_backup.db_api.delete_cron_trigger')
    @patch('openstack_dashboard.dashboards.custom_backup.db_api.create_cron_trigger')
    def test_update_cron_trigger_case_1(self, create_method, delete_method):
        """
        By mocking the delete_cron_trigger/create_cron_trigger methods we are implicitly mocking the mistral.api
        methods
        """
        backup_job = FakeBackUpJob()
        update_cron_trigger(self.request, backup_job, 'new-name')
        delete_method.assert_called_with(self.request, backup_job.name)
        create_method.assert_called_with(request=self.request,
                                         name='new-name',
                                         workflow_input=loads(backup_job.workflow_input),
                                         schedule_pattern=backup_job.schedule_pattern)

    @patch('openstack_dashboard.dashboards.custom_backup.db_api.delete_cron_trigger', return_value=False)
    @patch('openstack_dashboard.dashboards.custom_backup.db_api.create_cron_trigger')
    def test_update_cron_trigger_failure_case(self, create_method, delete_method):
        """"""
        backup_job = FakeBackUpJob()
        update_cron_trigger(self.request, backup_job, 'new-name')
        delete_method.assert_called_with(self.request, backup_job.name)
        create_method.assert_not_called()

    @patch('openstack_dashboard.dashboards.custom_backup.db_api.delete_cron_trigger')
    @patch('openstack_dashboard.dashboards.custom_backup.db_api.get_or_none', return_value=None)
    def test_delete_backup_job_when_obj_not_found(self, get_or_none, delete_cron_trigger):
        """
        Verify that no api call() is made when the BackupJob is not found
        """
        backup_job = FakeBackUpJob()
        delete_backup_job(self.request, backup_job)
        get_or_none.assert_called()
        delete_cron_trigger.assert_not_called()

    @patch('openstack_dashboard.dashboards.custom_backup.db_api.delete_cron_trigger')
    @patch('openstack_dashboard.dashboards.custom_backup.db_api.get_or_none', side_effect=MultipleObjectsReturned)
    def test_exception_is_handled(self, get_or_none, delete_cron_trigger):
        delete_backup_job(self.request, FakeBackUpJob())
        get_or_none.assert_called()
        delete_cron_trigger.assert_not_called()

    @patch('openstack_dashboard.dashboards.custom_backup.db_api.delete_cron_trigger', side_effect=APIException)
    @patch('openstack_dashboard.dashboards.custom_backup.db_api.get_or_none')
    def test_cron_trigger_error_is_handled(self, get_or_none, delete_cron_trigger):
        """
        Spying the delete() method to assert that the execution stops before it
        """
        obj = FakeBackUpJob()
        mocked_backup_job = MagicMock(spec=obj, wraps=obj)
        get_or_none.return_value = mocked_backup_job
        delete_backup_job(self.request, mocked_backup_job)
        get_or_none.assert_called()
        mocked_backup_job.delete.assert_not_called()

    @patch('openstack_dashboard.dashboards.custom_backup.db_api.get_notification', return_value=None)
    def test_get_backup_jobs_of_notification_empty_qs(self, get_notification):
        """Assert that an empty qs of the expected type gets returned"""
        qs = get_backup_jobs_of_notification('fake-id')
        self.assertFalse(qs.exists())
        self.assertTrue(qs.model is Notification)

    @patch('openstack_dashboard.dashboards.custom_backup.db_api.get_notification', return_value=None)
    def test_attempt_to_delete_not_existing_notification(self, get_notification):
        """Assert that the proper exception is Raised"""
        from horizon.exceptions import NotFound
        self.assertRaises(NotFound, delete_notification, 'fake-id')

    @patch('openstack_dashboard.dashboards.custom_backup.db_api.get_notification')
    def test_delete_notification_linked_to_backup(self, get_notification):
        """Assert that the proper exception is Raised"""
        from horizon.exceptions import HandledException
        mocked_notification = MagicMock(spec_set=Notification)
        get_notification.return_value = mocked_notification
        self.assertRaises(HandledException, delete_notification, 'fake-id')
