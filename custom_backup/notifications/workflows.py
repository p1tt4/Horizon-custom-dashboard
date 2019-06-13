import logging
from django.db import IntegrityError, transaction
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from horizon import forms, workflows, messages
from openstack_dashboard.dashboards.custom_backup.constants import constants
from openstack_dashboard.dashboards.custom_backup.db_api import create_notification, get_notification
from openstack_dashboard.dashboards.custom_backup.utils import cmp_dict, extract_object_id


logger = logging.getLogger(__name__)


class CreateNotificationAction(workflows.Action):
    name = forms.CharField(max_length=constants.STRING_L, widget=forms.widgets.TextInput(attrs={'autocomplete': 'off'}))
    sender_address = forms.EmailField(max_length=constants.STRING_L, widget=forms.widgets.EmailInput(attrs={'autocomplete': 'off'}))
    recipient_address = forms.EmailField(max_length=constants.STRING_L, widget=forms.widgets.EmailInput(attrs={'autocomplete': 'off'}))
    smtp_server = forms.GenericIPAddressField(widget=forms.widgets.TextInput(attrs={'autocomplete': 'off'}))
    openstack_url = forms.URLField(widget=forms.widgets.TextInput(attrs={'autocomplete': 'off'}))


class CreateNotificationStep(workflows.Step):
    action_class = CreateNotificationAction
    contributes = ('name', 'sender_address', 'recipient_address', 'smtp_server', 'openstack_url')


class CreateNotificationWorkflow(workflows.Workflow):
    slug = "create_notification"
    name = _("Create Notification")
    finalize_button_name = _("Create")
    success_message = _("Created Notification")
    failure_message = _("Unable to create Notification")
    default_steps = (CreateNotificationStep,)
    wizard = True

    def get_success_url(self):
        return reverse('horizon:custom_backup:notifications:index')

    def _fail_to_create(self):
        msg = _("Unable to create Notification")
        messages.error(self.request, msg)
        return False

    @transaction.atomic
    def handle(self, request, data):
        """
        the first loc verifies that the unique-together constraint is respected. In this case, with respect to update
        it must be guaranteed that no other element with the same tuple exists.

        :param request: the HTTP-Request object
        :param data: dictionary holding all form's data
        :return: True/False whether the creation succeeded/failed
        """
        if get_notification(name=self.context['name'], sender_address=self.context['sender_address'],
                            recipient_address=self.context['recipient_address']) is not None:
            msg = _("A notification with the same Name-Sender-Recipient already exists")
            logger.error(msg)
            self.failure_message = msg
            return False

        try:
            notification = create_notification(
                name=data.get('name'),
                sender_address=data.get('sender_address'),
                recipient_address=data.get('recipient_address'),
                smtp_server=data.get('smtp_server'),
                openstack_url=data.get('openstack_url')
            )
        except (IntegrityError, ValueError) as e:
            logger.error(e)
            return False

        return notification is not None


class UpdateNotificationAction(CreateNotificationAction):

    def __init__(self, request, context, *args, **kwargs):
        super(UpdateNotificationAction, self).__init__(request, context, *args, **kwargs)
        current_notification = get_notification(id=extract_object_id(request))
        for field_name, field in self.fields.items():
            field.required = False
            if hasattr(current_notification, field_name):
                field.initial = getattr(current_notification, field_name)


class UpdateNotificationStep(workflows.Step):
    action_class = UpdateNotificationAction
    contributes = ('name', 'sender_address', 'recipient_address', 'smtp_server', 'openstack_url')


class UpdateNotificationWorkflow(workflows.Workflow):
    slug = "update_notification"
    name = _("Update Notification")
    finalize_button_name = _("Save")
    success_message = _("Updated Notification %s")
    failure_message = _("Unable to update Notification")
    default_steps = (UpdateNotificationStep,)
    wizard = True

    def get_success_url(self):
        return reverse('horizon:custom_backup:notifications:index')

    @property
    def get_object(self):
        return get_notification(id=extract_object_id(self.request))

    def data_has_changed(self):
        obj = self.get_object
        changed = list()
        for k, v in self.context.items():
            if v and getattr(obj, k) != v:
                changed.append(k)
        return changed

    @property
    def existing_notification(self):
        return get_notification(
            name=self.context['name'] or self.get_object.name,
            sender_address=self.context['sender_address'] or self.get_object.sender_address,
            recipient_address=self.context['recipient_address'] or self.get_object.recipient_address
        )

    def handle(self, request, data):
        """
        Verify that no other record, but the current, with the same tuple (name-sender-recipient) exists

        :param request: the HTTP-Request object
        :param data: dictionary holding all form's data
        :return: True/False whether the creation succeeded/failed
        """
        changed_fields = self.data_has_changed()
        if not changed_fields:
            self.success_message = _("Nothing has changed")
            return True

        if self.existing_notification and self.existing_notification != self.get_object:
            msg = _("A notification with the same Name-Sender-Recipient already exists")
            logger.error(msg)
            self.failure_message = msg
            return False

        o = self.get_object
        for f in changed_fields:
            setattr(o, f, self.context[f])
        o.save()
        return True
