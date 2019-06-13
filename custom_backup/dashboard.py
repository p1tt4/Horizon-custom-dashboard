from django.utils.translation import ugettext_lazy as _

import horizon


class Custom_Backup(horizon.Dashboard):
    name = _("Custom_Backup")
    slug = "custom_backup"
    panels = ('jobs', 'notifications')
    # Specify the slug of the dashboard's default panel.
    default_panel = 'jobs'


horizon.register(Custom_Backup)
