from json import dumps, loads
from uuid import uuid1
from django.contrib.auth.models import User
from django.utils import timezone
from django.test import RequestFactory

from mock import patch, MagicMock
from django.core.urlresolvers import reverse
from openstack_dashboard.test.helpers import TestCase, APITestCase

from openstack_dashboard.dashboards.custom_backup.models import BackupJob, Notification
from openstack_dashboard.dashboards.custom_backup.tests import MockTriggerObject
from openstack_dashboard.dashboards.custom_backup.jobs.tables import DeleteBackupJob
from openstack_dashboard.dashboards.custom_backup.notifications.tables import DeleteNotification


class BackupWorkflowTestCase(TestCase):

    def setUp(self):
        super(BackupWorkflowTestCase, self).setUp()
        self.backup_job = BackupJob.objects.create(
            name='New BackupJob',
            workflow_input=dumps({
                'instance_pause': False,
                'instance_stop': True,
                'pattern': "{0}_backup_{1}",
                'instance': str(uuid1()),
                'only_os': False,
                'cinder_backup': False,
                'max_snapshots': 2,
                'max_backups': 0,
                'only_backup': True,
                'backup_type': False,
                'metadata': None
            }),
            schedule_pattern="* * * * *",
            creation_time=timezone.now(),
            cron_trigger_id=str(uuid1()),
            project_id=10,
            notification=None
        )

    @patch('openstack_dashboard.dashboards.custom_backup.db_api.create_cron_trigger', return_value=MockTriggerObject())
    def test_backup_clone_unique_name_case(self, create_cron_trigger):
        """"""
        self.client.post(
            reverse('horizon:custom_backup:jobs:clone', args=[self.backup_job.id]),
            data={'name': 'this is a clone'}
        )
        create_cron_trigger.assert_called()
        self.assertTrue(BackupJob.objects.filter(name='this is a clone').exists())

    @patch('openstack_dashboard.dashboards.custom_backup.db_api.create_cron_trigger', return_value=MockTriggerObject())
    def test_backup_clone_same_name_case(self, create_cron_trigger):
        """"""
        self.client.post(
            reverse('horizon:custom_backup:jobs:clone', args=[self.backup_job.id]),
            data={'name': 'New BackupJob'}
        )
        create_cron_trigger.assert_not_called()
        self.assertEqual(BackupJob.objects.filter(name='New BackupJob').count(), 1)

    @patch('openstack_dashboard.dashboards.custom_backup.db_api.delete_cron_trigger', return_value=True)
    def test_backup_delete(self, delete_cron_trigger):
        """
        There is not need to mock Nova call, because no-one is made, instead by mocking the above method, we avoid
        call to Mistral. Instead we keep connection to DB up
        """
        DeleteBackupJob().action(self.request, self.backup_job.id)
        delete_cron_trigger.assert_called()
        self.assertRaises(BackupJob.DoesNotExist, self.backup_job.refresh_from_db)


class NovaMockBackupWorkflowTestCase(APITestCase):

    def setUp(self):
        super(NovaMockBackupWorkflowTestCase, self).setUp()
        self.servers_list = self.servers.list()
        novaclient = self.stub_novaclient()
        novaclient.servers = self.mox.CreateMockAnything()
        novaclient.versions = self.mox.CreateMockAnything()
        novaclient.versions.get_current().AndReturn("2.45")
        novaclient.servers.list(True, {'all_tenants': True}).AndReturn(self.servers_list)
        self.mox.ReplayAll()

    @patch('openstack_dashboard.dashboards.custom_backup.db_api.create_cron_trigger', return_value=MockTriggerObject())
    def test_backup_create(self, create_cron_trigger):
        """
        Perform an API call to a mocked Nova backend, while Mistral API are mocked, create a new object in the Database
        """
        payload = {'name': 'integration backup', 'instance': self.servers_list[0].id}
        self.client.post(reverse('horizon:custom_backup:jobs:create'), data=payload)
        self.assertEqual(BackupJob.objects.count(), 1)
        self.assertEqual(BackupJob.objects.first().name, 'integration backup')

    @patch('openstack_dashboard.dashboards.custom_backup.db_api.delete_cron_trigger', return_value=True)
    @patch('openstack_dashboard.dashboards.custom_backup.db_api.create_cron_trigger', return_value=MockTriggerObject())
    def test_backup_update(self, cron_trigger, delete_cron_trigger):
        notification = Notification.objects.create(**{
            'name': 'new_notification', 'sender_address': 'sender@email.com', 'recipient_address': 'recipient@email.com',
            'smtp_server': '1.1.1.1', 'openstack_url': 'http://website.com'
        })

        new_backup_job = BackupJob.objects.create(
            name='New BackupJob',
            workflow_input=dumps({
                'instance_pause': False,
                'instance_stop': True,
                'pattern': "{0}_backup_{1}",
                'instance': self.servers_list[0].id,
                'only_os': False,
                'cinder_backup': False,
                'max_snapshots': 2,
                'max_backups': 0,
                'only_backup': True,
                'backup_type': False,
                'metadata': None
            }),
            schedule_pattern="* * * * *",
            creation_time=timezone.now(),
            cron_trigger_id=str(uuid1()),
            project_id=10,
            notification=None
        )

        workflow_before = loads(new_backup_job.workflow_input)
        self.client.post(
            reverse('horizon:custom_backup:jobs:update', args=[new_backup_job.id]),
            data={'name': new_backup_job.name ,'instance': self.servers_list[1].id, 'notification': notification.id}
        )
        delete_cron_trigger.assert_called()
        new_backup_job.refresh_from_db()
        self.assertNotEqual(new_backup_job.workflow_input, workflow_before)
        self.assertEqual(new_backup_job.notification, notification)


class NotificationWorkflowTestCase(TestCase):

    def test_notification_create(self):
        self.client.post(
            reverse('horizon:custom_backup:notifications:create'),
            data={'name': 'new_notification', 'sender_address': 'sender@email.com',
                  'recipient_address': 'recipient@email.com', 'smtp_server': '1.1.1.1',
                  'openstack_url': 'http://website.com'}
        )
        self.assertTrue(Notification.objects.filter(name='new_notification').exists())

    def test_notification_update(self):
        notification = Notification.objects.create(**{
            'name': 'new_notification', 'sender_address': 'sender@email.com',
            'recipient_address': 'recipient@email.com', 'smtp_server': '1.1.1.1',
            'openstack_url': 'http://website.com'
        })
        self.client.post(
            reverse('horizon:custom_backup:notifications:update', args=[notification.id]),
            data={'name': 'modified name'}
        )
        self.assertTrue(Notification.objects.filter(name='modified name').exists())

    def test_notification_update_same_name(self):
        for i in range(2):
            Notification.objects.create(**{
                'name': "new-notification-{}".format(i), 'sender_address': 'sender@email.com',
                'recipient_address': 'recipient@email.com', 'smtp_server': '1.1.1.1',
                'openstack_url': 'http://website.com'
            })

        self.client.post(
            reverse('horizon:custom_backup:notifications:update', args=[Notification.objects.last().id]),
            data={'name': "new-notification-{}".format(0)}
        )
        self.assertEqual(Notification.objects.filter(name='new-notification-0').count(), 1)

    def test_notification_of_backup_job_delete(self):

        notification = Notification.objects.create(**{
            'name': "new-notification", 'sender_address': 'sender@email.com',
            'recipient_address': 'recipient@email.com', 'smtp_server': '1.1.1.1',
            'openstack_url': 'http://website.com'
        })

        BackupJob.objects.create(
            name='New BackupJob',
            workflow_input=dumps({
                'instance_pause': False,
                'instance_stop': True,
                'pattern': "{0}_backup_{1}",
                'instance': str(uuid1()),
                'only_os': False,
                'cinder_backup': False,
                'max_snapshots': 2,
                'max_backups': 0,
                'only_backup': True,
                'backup_type': False,
                'metadata': None
            }),
            schedule_pattern="* * * * *",
            creation_time=timezone.now(),
            cron_trigger_id=str(uuid1()),
            project_id=10,
            notification=notification
        )
        # import pdb;pdb.set_trace()
        DeleteNotification().action(self.request, notification.id)
        notification.refresh_from_db()
        self.assertIsNotNone(notification)