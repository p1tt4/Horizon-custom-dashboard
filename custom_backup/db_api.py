import logging
from uuid import uuid1
from json import loads, dumps
from django.core.exceptions import MultipleObjectsReturned
from django.db import IntegrityError
from django.utils import timezone
from horizon.exceptions import HandledException, NotFound
from mistraldashboard import api
from mistralclient.api.base import APIException
from openstack_dashboard.dashboards.custom_backup.models import BackupJob, Notification
from openstack_dashboard.dashboards.custom_backup.constants import constants


logger = logging.getLogger(__name__)


# TODO can it be used?
# @memoized.memoized_method
def get_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist as e:
        logger.error(e)
        return None
    except MultipleObjectsReturned as e:
        logger.error(e)
        raise e


def create_cron_trigger(request, name, workflow_input, schedule_pattern):
    trigger_params = ''
    trigger_first_time = None
    default_count = None
    default_workflow_id = constants.DEFAULT_WORKFLOW_ID
    trigger_name = constants.NAME_PREFIX.format(name)
    try:
        logger.info("Creating cron-trigger {}".format(trigger_name))
        new_trigger = api.cron_trigger_create(
            request,
            trigger_name,
            default_workflow_id,
            workflow_input,
            trigger_params,
            schedule_pattern,
            trigger_first_time,
            default_count,
        )
        return new_trigger
    except APIException as e:
        logger.error(e)
        raise e


def delete_cron_trigger(request, backup_job_name):
    trigger_name = constants.NAME_PREFIX.format(backup_job_name)
    try:
        logger.info("Deleting cron-trigger {}".format(trigger_name))
        api.cron_trigger_delete(request, trigger_name)
        return True
    except APIException as e:
        logger.error(e)
        raise


def update_cron_trigger(request, current_backup_job, new_name='', schedule_pattern=None, workflow_input=None):
    """
    A cron-trigger is always deleted, because it cannot be modified, even if we are changing its name only.

    :param current_backup_job: triggers are identified using the backup_job_name
    :param new_name: triggers are identified using the backup_job_name
    :param schedule_pattern: this is a string
    :param workflow_input: it must be a dictionary, not a string. Mistral stores this information as JSON type
    TODO: if loads raises Exception then it should be handled (check usage of @handle_error decorator in api)
    """
    if not workflow_input:
        workflow_input = current_backup_job.workflow_input
    if not schedule_pattern:
        schedule_pattern = current_backup_job.schedule_pattern

    if isinstance(workflow_input, str) or isinstance(workflow_input, unicode):
        workflow_input = loads(workflow_input)

    current_name = current_backup_job.name
    if delete_cron_trigger(request, current_name):
        trigger_name = new_name or current_name
        return create_cron_trigger(request=request,
                                   name=trigger_name,
                                   workflow_input=workflow_input,
                                   schedule_pattern=schedule_pattern)
    return None


def create_backup_job(request, name, workflow_input, schedule_pattern, tenant_id, notification):
    """
    NOTE: remind to use @transaction.atomic inside the caller
    :return:
    """
    # new_trigger = create_cron_trigger(request, name, workflow_input, schedule_pattern)
    try:
        # logger.info("Creating new BackupJob associated with trigger: {}".format(new_trigger.id))
        return BackupJob.objects.create(
            name=name,
            workflow_input=dumps(workflow_input),
            schedule_pattern=schedule_pattern,
            creation_time=timezone.now(),
            cron_trigger_id="43d345e0-fdfb-4639-8b78-cfcbc68846e0",
            project_id=tenant_id,
            notification=notification
        )
    except IntegrityError as e:
        logger.error(e)
        raise


def delete_backup_job(request, backup_job_id):
    try:
        logger.info("Trying to delete BackupJob: {}".format(backup_job_id))
        obj = get_or_none(BackupJob, id=backup_job_id)
        if not obj:
            return False
        delete_cron_trigger(request, obj.name)
        obj.delete()
    except (IntegrityError, MultipleObjectsReturned, APIException) as e:
        logger.error("Failed to delete BackupJob with ID {}: {}".format(backup_job_id, e))
        return False
    else:
        return True


def all_backup_jobs(as_list=False):
    qs = BackupJob.objects.all()
    if as_list:
        return list(qs)
    return qs


def get_backup_job(**kwargs):
    return get_or_none(BackupJob, **kwargs)


def list_notifications(as_list=False):
    qs = Notification.objects.all()
    if as_list:
        return list(qs)
    return qs


def create_notification(name, sender_address, recipient_address, smtp_server, openstack_url):
    try:
        return Notification.objects.create(
            name=name,
            sender_address=sender_address,
            recipient_address=recipient_address,
            smtp_server=smtp_server,
            openstack_url=openstack_url
        )
    except IntegrityError as e:
        logger.error(e)
        raise e


def get_notification(**kwargs):
    return get_or_none(Notification, **kwargs)


def get_backup_jobs_of_notification(notification_id):
    """
    An empty queryset is generated to ensure that this method always returns a QuerySet
    """
    empty_qs = Notification.objects.none()
    notification_obj = get_notification(id=notification_id)
    if not notification_obj:
        return empty_qs
    return notification_obj.backupjob_set.all()


def delete_notification(notification_id):
    from horizon.exceptions import NotFound
    notification_obj = get_notification(id=notification_id)
    if not notification_obj:
        raise NotFound("Notification does not exists")

    if notification_obj and notification_obj.backupjob_set.exists():
        raise HandledException("Notification is linked to existing backup jobs")
    logger.info("Trying to delete Notification with id: {}".format(notification_obj.id))
    notification_obj.delete()
