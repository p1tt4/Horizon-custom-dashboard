import logging
from json import loads, dumps
from django.db import IntegrityError, transaction
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from horizon import exceptions, workflows, forms, messages
from openstack_dashboard.api.nova import server_list as nova_server_list
from openstack_dashboard.dashboards.custom_backup.constants import constants
from openstack_dashboard.dashboards.custom_backup.db_api import create_backup_job, update_cron_trigger, \
    get_backup_job, list_notifications, get_notification, all_backup_jobs
from openstack_dashboard.dashboards.custom_backup.utils import cmp_dict, extract_object_id

logger = logging.getLogger(__name__)


# cmp_dict function is assigned to variable for expressiveness
workflow_are_equal = cmp_dict


#  TODO: it'd be nice to implement some kind of Model based Workflow.Action, to validate the fields easily
class WorkflowActionBase(workflows.Action):

    def perform_unique_check(self, field_name):
        """overridden in subclasses"""
        pass

    @property
    def current_object_id(self):
        return extract_object_id(self.request)

    @property
    def _creation_state(self):
        return self.current_object_id is None

    def is_valid(self):
        is_valid = super(WorkflowActionBase, self).is_valid()
        for form_field_name, form_field in self.fields.items():
            if hasattr(form_field, 'unique') and form_field.unique:
                self.perform_unique_check(form_field_name)

        return is_valid and not self.errors


class UniqueCharField(forms.CharField):
    unique = False

    def __init__(self, max_length=None, min_length=None, strip=True, empty_value='', *args, **kwargs):
        self.unique = kwargs.pop('unique', False)
        super(UniqueCharField, self).__init__(max_length, min_length, strip, empty_value, *args, **kwargs)


class NameAction(WorkflowActionBase):
    name = UniqueCharField(max_length=constants.UUID_MAX_LEN, required=False, strip=True, unique=True)
    metadata_key = forms.CharField(max_length=constants.STRING_XXS, required=False)
    metadata_value = forms.CharField(max_length=constants.STRING_XXS, required=False)
    # NOTE: if instance field is renamed this change must also be reflected inside the template, because it's used
    # to render the select menu
    instance = forms.ChoiceField(required=False)
    # this field is created/used inside template only to address ValidationError rendering: i.e. all validatior
    # error are appended to this field, so that are displayed in the same place.
    # IMPORTANT NOTE: if the name is changed then it also must be updated inside the custom_backup.css file,
    # otherwise, the error field will be visible also when everything is correct.
    error_field = forms.CharField(required=False)

    class Meta(object):
        name = _("Name ")

    # TODO to comment
    def perform_unique_check(self, field_name):
        qs = all_backup_jobs().filter(**{field_name: self.cleaned_data.get(field_name)})
        if not self._creation_state:
            qs = qs.exclude(id=self.current_object_id)

        if qs.exists():
            self.errors['error_field'] = _("Another BackupJob has this name. Please change this field")

    def clean(self):
        cleaned_data = super(NameAction, self).clean()
        if not cleaned_data["name"]:
            raise forms.ValidationError({'error_field': _("Name field is required")})
        if (not cleaned_data["instance"] and not cleaned_data['metadata_value'] and not cleaned_data['metadata_key']) \
                or (not cleaned_data['instance'] and not (cleaned_data['metadata_key'] and cleaned_data['metadata_value'])):
            raise forms.ValidationError({
                'error_field': _("Source field is required. Provide a metadata key-value pair or select one instance")
            })
        elif cleaned_data["instance"] and cleaned_data['metadata_value'] and cleaned_data['metadata_key']:
            raise forms.ValidationError({
                'error_field': _("Only one source input can be provided, either Metadata or Instance")
            })
        elif (cleaned_data['metadata_value'] and not cleaned_data['metadata_key']) or (
                not cleaned_data['metadata_value'] and cleaned_data['metadata_key']):
            raise forms.ValidationError({
                'error_field': _("Ensure you filled both metadata key and value")
            })
        cleaned_data.pop('error_field')
        return cleaned_data

    def __init__(self, request, *args, **kwargs):
        super(NameAction, self).__init__(request, *args, **kwargs)
        # server_list, _more_data = nova_server_list(request, search_opts={'all_tenants': True})
        self.fields['instance'].choices = [
            ('', ''),
            (u'43d345e0-fdfb-4639-8b78-cfcbc68846e0', u'cento'),
            (u'5a8e1eda-3d8b-46f6-aed3-e23a257a41ed', u'aba1b8fe-394f-4732-a876-f54f0d152eb2'),
            (u'4f21ce60-6925-4841-8855-5742be1fd49b', u'win02'),
            (u'3807a5a0-3a06-4c20-b3c1-2a2b122660c1', u'Development-Box'),
            (u'6ef0a200-f0df-4453-9f8c-cc92a3cc9ac0', u'gerrit1'),
            (u'13f3f6b3-b9a4-46b6-893e-fb6b8193ca71', u'lab-gateway')
        ]



class InputAction(workflows.Action):
    stop_instance = forms.BooleanField(required=False)
    pause_instance = forms.BooleanField(required=False)
    # backup mode is the cynder_backup parameter inside the workflow
    backup_mode = forms.BooleanField(required=False)
    preserve_snapshot = forms.BooleanField(required=False)
    max_backups = forms.IntegerField(
        min_value=constants.MIN_BACKUP_VALUE,
        max_value=constants.MAX_BACKUP_VALUE,
        required=False,
    )
    max_snapshots = forms.IntegerField(
        min_value=constants.MIN_SNAPSHOT_VALUE,
        max_value=constants.MAX_SNAPSHOT_VALUE,
        required=False,
    )
    backup_type = forms.ChoiceField(required=False, choices=constants.BACKUP_TYPE_CHOICES)

    class Meta(object):
        name = _("Workflow Input")


class ScheduleAction(workflows.Action):
    minute = forms.ChoiceField(
        label=_("Minute"),
        required=False,
        choices=tuple([('*', '*')] + [(str(i), str(i)) for i in range(constants.MINUTES_PER_HOUR)]),
    )
    hour = forms.ChoiceField(
        label=_("Hour"),
        required=False,
        choices=tuple([('*', '*')] + [(str(i), str(i)) for i in range(constants.HOURS_PER_DAY)]),
    )
    day = forms.ChoiceField(
        label=_("Day"),
        required=False,
        choices=tuple([('*', '*')] + [(str(i+1), str(i+1)) for i in range(constants.DAYS_PER_MONTH)]),
    )
    month = forms.ChoiceField(
        label=_("Month"),
        required=False,
        choices=tuple([(i, name[:3]) for i, name in constants.MONTH_CHOICES]),
    )
    weekday = forms.ChoiceField(
        label=_("Weekday"),
        required=False,
        choices=tuple([(i, name[:3]) for i, name in constants.WEEKDAY_CHOICES]),
    )

    class Meta(object):
        name = _("Cron schedule")


class CreateBackupJobNameStep(workflows.Step):
    action_class = NameAction
    contributes = ("name", "metadata_key", "metadata_value", "instance", )
    template_name = 'custom_backup/jobs/create_backup_job/backup_name.html'


class CreateBackupInputStep(workflows.Step):
    action_class = InputAction
    contributes = ("stop_instance", "pause_instance", "backup_mode", "preserve_snapshot",
                   "max_backups", "max_snapshots", 'backup_type')
    template_name = 'custom_backup/jobs/create_backup_job/backup_input.html'


class CreateBackupScheduleStep(workflows.Step):
    action_class = ScheduleAction
    contributes = ("minute", "hour", "day", "month", "weekday")
    template_name = 'custom_backup/jobs/create_backup_job/backup_schedule.html'


class CreateBackupNotificationAction(workflows.Action):
    notification = forms.ChoiceField(required=False)

    def __init__(self, request, *args, **kwargs):
        super(CreateBackupNotificationAction, self).__init__(request, *args, **kwargs)
        self.fields['notification'].choices = [('', '')] + [(notif.id, notif.name) for notif in list_notifications()]

    class Meta(object):
        name = _("Notification")


class CreateBackupNotificationStep(workflows.Step):
    action_class = CreateBackupNotificationAction
    contributes = ("notification", )
    template_name = 'custom_backup/jobs/create_backup_job/backup_notification.html'


class CreateBackupJobWorkflow(workflows.Workflow):
    slug = "create_backup_job"
    name = _("Create BackupJob")
    finalize_button_name = _("Create")
    success_message = _('Created BackupJob "%s"')
    failure_message = _('Unable to create BackupJob')
    default_steps = (CreateBackupJobNameStep,
                     CreateBackupInputStep,
                     CreateBackupScheduleStep,
                     CreateBackupNotificationStep)
    wizard = True

    def get_success_url(self):
        return reverse('horizon:custom_backup:jobs:index')

    def _fail_to_create(self):
        msg = _("Unable to create BackupJob")
        messages.error(self.request, msg)
        return False

    @transaction.atomic
    def handle(self, request, context):
        """
        Validation is executed at dispatch time, before the execution reaches the current method.
        :return: True if the creations succeeds, False otherwise
        """
        if not self.is_valid():
            return False

        schedule_pattern = "{} {} {} {} {}".format(
            context['minute'] or '*',
            context['hour'] or '*',
            context['day'] or '*',
            context['month'] or '*',
            context['weekday'] or '*',
        )

        workflow_input = {
            'instance_pause': context['pause_instance'],
            'instance_stop': context['stop_instance'],
            'pattern': "{0}_backup_{1}",
            'instance': context['instance'] or None,
            'only_os': False,
            'cinder_backup': context['backup_mode'],
            'max_snapshots': context['max_snapshots'],
            'max_backups': context['max_backups'],
            'only_backup': not context['preserve_snapshot'],
            'backup_type': context['backup_type'],
            'metadata': {
                'key': context['metadata_key'],
                'value': context['metadata_value']
                } if context['metadata_key'] else None
        }

        try:
            new_backup = create_backup_job(
                request=request,
                name=context.get('name'),
                workflow_input=workflow_input,
                schedule_pattern=schedule_pattern,
                tenant_id=self.request.user.tenant_id,
                notification=get_notification(id=context.get('notification'))
            )
        except (IntegrityError, ValueError) as e:
            logger.error(e)
            return False

        return new_backup is not None


class UpdateNameAction(NameAction):
    """"""

    def __init__(self, request, context, *args, **kwargs):
        super(UpdateNameAction, self).__init__(request, context, *args, **kwargs)
        current_backup = get_backup_job(id=extract_object_id(request))
        if not current_backup:
            raise exceptions.NotAvailable("Object not found")
        self.fields['name'].initial = current_backup.name
        workflow_input = loads(current_backup.workflow_input)
        self.fields['instance'].initial = workflow_input.get('instance')
        metadata = workflow_input.get('metadata')
        self.fields['metadata_key'].initial = metadata['key'] if metadata else ''
        self.fields['metadata_value'].initial = metadata['value'] if metadata else ''


class UpdateBackupJobNameStep(workflows.Step):
    action_class = UpdateNameAction
    contributes = ("name", "metadata_key", "metadata_value", "instance", )
    template_name = 'custom_backup/jobs/update_backup_job/backup_name.html'


class UpdateInputAction(InputAction):
    """"""

    def __init__(self, request, context, *args, **kwargs):
        super(UpdateInputAction, self).__init__(request, context, *args, **kwargs)
        current_backup = get_backup_job(id=extract_object_id(request))
        if not current_backup:
            raise exceptions.NotAvailable("Object not found")
        workflow_input = loads(current_backup.workflow_input)
        self.fields['stop_instance'].initial = workflow_input['instance_stop']
        self.fields['pause_instance'].initial = workflow_input['instance_pause']
        self.fields['max_snapshots'].initial = int(workflow_input['max_snapshots']) if workflow_input['max_snapshots'] else 0
        self.fields['max_backups'].initial = int(workflow_input['max_backups']) if workflow_input['max_backups'] else 0
        self.fields['preserve_snapshot'].initial = not workflow_input['only_backup']
        self.fields['backup_type'].initial = workflow_input['backup_type']
        self.fields['backup_mode'].initial = workflow_input['cinder_backup']


class UpdateBackupInputStep(workflows.Step):
    action_class = UpdateInputAction
    contributes = ("stop_instance", "pause_instance", "backup_mode", "preserve_snapshot",
                   "max_backups", "max_snapshots", 'backup_type')
    template_name = 'custom_backup/jobs/update_backup_job/backup_input.html'


class UpdateScheduleAction(ScheduleAction):
    """"""
    def __init__(self, request, context, *args, **kwargs):
        super(UpdateScheduleAction, self).__init__(request, context, *args, **kwargs)
        current_backup = get_backup_job(id=extract_object_id(request))
        if not current_backup:
            # TODO to improve
            raise exceptions.NotAvailable("Object not found")

        pattern_array = current_backup.schedule_pattern.split(' ')
        self.fields['minute'].initial = pattern_array[0]
        self.fields['hour'].initial = pattern_array[1]
        self.fields['day'].initial = pattern_array[2]
        self.fields['month'].initial = pattern_array[3]
        self.fields['weekday'].initial = pattern_array[4]


class UpdateBackupScheduleStep(workflows.Step):
    action_class = UpdateScheduleAction
    contributes = ("minute", "hour", "day", "month", "weekday", )
    template_name = 'custom_backup/jobs/update_backup_job/backup_schedule.html'


class UpdateBackupNotificationAction(workflows.Action):
    notification = forms.CharField(max_length=constants.UUID_MAX_LEN, required=False)

    def __init__(self, request, *args, **kwargs):
        super(UpdateBackupNotificationAction, self).__init__(request, *args, **kwargs)
        current_backup = get_backup_job(id=extract_object_id(request))
        if not current_backup:
            raise exceptions.NotAvailable("Object not found")
        self.fields['notification'].choices = [('', '')] + [(notif.id, notif.name) for notif in list_notifications()]
        self.fields['notification'].initial = current_backup.notification.id if current_backup.notification else ''

    class Meta(object):
        name = _("Notification")


class UpdateBackupNotificationStep(workflows.Step):
    action_class = UpdateBackupNotificationAction
    contributes = ("notification", )
    template_name = 'custom_backup/jobs/create_backup_job/backup_notification.html'


class UpdateBackupJob(workflows.Workflow):
    slug = "update_backup_job"
    name = _("Modify BackupJob")
    finalize_button_name = _("Save")
    success_message = _("Successfully modified BackupJob %s")
    failure_message = _("Unable to update BackupJob")
    default_steps = (UpdateBackupJobNameStep,
                     UpdateBackupInputStep,
                     UpdateBackupScheduleStep,
                     UpdateBackupNotificationStep)
    wizard = True

    def get_initial(self):
        initial = dict()
        obj = self.context['current_backup_job']
        schedule_pattern_array = obj.schedule_pattern.split(' ')
        initial['minute'] = schedule_pattern_array[0]
        initial['hour'] = schedule_pattern_array[1]
        initial['day'] = schedule_pattern_array[2]
        initial['month'] = schedule_pattern_array[3]
        initial['weekday'] = schedule_pattern_array[4]
        initial['workflow_input'] = obj.workflow_input
        initial['name'] = obj.name
        return initial

    def get_success_url(self):
        return reverse('horizon:custom_backup:jobs:index')

    @transaction.atomic
    def handle(self, request, context):
        current_backup_job = get_backup_job(id=extract_object_id(request))
        new_schedule_pattern = "{} {} {} {} {}".format(
            context['minute'], context['hour'], context['day'], context['month'], context['weekday'],
        )
        new_workflow_input = {
            'instance_pause': context['pause_instance'],
            'instance_stop': context['stop_instance'],
            'pattern': "{0}_backup_{1}",
            'instance': context['instance'] or None,
            'only_os': False,
            'cinder_backup': context['backup_mode'],
            'max_snapshots': context['max_snapshots'],
            'max_backups': context['max_backups'],
            'only_backup': not context['preserve_snapshot'],
            'backup_type': context['backup_type'],
            'metadata': {
                'key': context['metadata_key'],
                'value': context['metadata_value']
                } if context['metadata_key'] else None
        }

        changed_data = current_backup_job.schedule_pattern != new_schedule_pattern
        changed_data = changed_data or not workflow_are_equal(loads(current_backup_job.workflow_input), new_workflow_input)
        changed_data = changed_data or current_backup_job.name != context.get('name')
        # if notification is not selected then it will be equal to the empty string and thus notification_value will
        # get the None value
        notification_value = context.get('notification') or None
        changed_data = changed_data or (current_backup_job.notification != notification_value)
        if not changed_data:
            return True

        new_trigger = update_cron_trigger(request=self.request,
                                          current_backup_job=current_backup_job,
                                          new_name=context.get('name'),
                                          schedule_pattern=new_schedule_pattern,
                                          workflow_input=new_workflow_input)
        setattr(current_backup_job, 'cron_trigger_id', new_trigger.id)
        current_backup_job.workflow_input = dumps(new_workflow_input)
        current_backup_job.schedule_pattern = new_schedule_pattern
        current_backup_job.name = context.get('name')
        current_backup_job.notification = get_notification(id=context.get('notification'))
        current_backup_job.update_time = timezone.now()
        current_backup_job.save()
        return True


class CloneBackupJobNameAction(WorkflowActionBase):
    name = UniqueCharField(required=False, unique=True)

    def __init__(self, request, *args, **kwargs):
        super(CloneBackupJobNameAction, self).__init__(request, *args, **kwargs)
        current_backup = get_backup_job(id=extract_object_id(request))
        if not current_backup:
            raise exceptions.NotAvailable("Object not found")
        self.fields['name'].initial = constants.BACKUP_CLONE_DEFAULT_NAME_PATTERN.format(current_backup.name)

    def perform_unique_check(self, field_name):
        qs = all_backup_jobs().filter(**{field_name: self.cleaned_data.get(field_name)})
        if qs.exists():
            self.errors['error_field'] = _("Another BackupJob has this name. Please change this field")


class CloneBackupJobNameStep(workflows.Step):
    action_class = CloneBackupJobNameAction
    contributes = ("name", )


class CloneBackupJob(workflows.Workflow):
    slug = "clone_backup_job"
    name = _("Clone BackupJob")
    finalize_button_name = _("Clone")
    success_message = _("Successfully cloned BackupJob %s")
    failure_message = _("Unable to clone BackupJob")
    default_steps = (CloneBackupJobNameStep,)
    wizard = True

    def get_success_url(self):
        return reverse('horizon:custom_backup:jobs:index')

    @transaction.atomic
    def handle(self, request, context):
        if not self.is_valid():
            return False

        current_backup = get_backup_job(id=extract_object_id(request))
        try:
            new_backup = create_backup_job(
                request=request,
                name=context.get('name'),
                workflow_input=loads(current_backup.workflow_input),
                schedule_pattern=current_backup.schedule_pattern,
                tenant_id=self.request.user.tenant_id,
                notification=current_backup.notification
            )
        except (IntegrityError, ValueError) as e:
            logger.error(e)
            return False

        return new_backup is not None
