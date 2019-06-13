from django.utils.translation import ugettext_lazy as _


class ConstantsWrapper(object):

    NAME_PREFIX = "Cron Trigger for Backup {}"

    DEFAULT_WORKFLOW_ID = 'custom_instance_backup.custom_instance_backup'

    STRING_XXS = 10
    STRING_XS = 25
    STRING_S = 50
    STRING_M = 100
    STRING_L = 200
    STRING_XL = 400
    STRING_XXL = 800
    STRING_XXXL = 1600

    UUID_MAX_LEN = 36
    PROJECT_ID_LEN = 32

    # the following constant values are used to populate options lists inside CreateBackupScheduleStep
    MINUTES_PER_HOUR = 60
    HOURS_PER_DAY = 24
    DAYS_PER_MONTH = 31

    WEEKDAY_MONDAY = _("Monday")
    WEEKDAY_TUESDAY = _("Tuesday")
    WEEKDAY_WEDNESDAY = _("Wednesday")
    WEEKDAY_THURSDAY = _("Thursday")
    WEEKDAY_FRIDAY = _("Friday")
    WEEKDAY_SATURDAY = _("Saturday")
    WEEKDAY_SUNDAY = _("Sunday")
    WEEKDAY_CHOICES = (
        ("*", "*"),
        ('1', WEEKDAY_MONDAY),
        ('2', WEEKDAY_TUESDAY),
        ('3', WEEKDAY_WEDNESDAY),
        ('4', WEEKDAY_THURSDAY),
        ('5', WEEKDAY_FRIDAY),
        ('6', WEEKDAY_SATURDAY),
        ('7', WEEKDAY_SUNDAY)
    )

    MONTH_JANUARY = _("January")
    MONTH_FEBRUARY = _("February")
    MONTH_MARCH = _("March")
    MONTH_APRIL = _("April")
    MONTH_MAY = _("May")
    MONTH_JUNE = _("June")
    MONTH_JULY = _("July")
    MONTH_AUGUST = _("August")
    MONTH_SEPTEMBER = _("September")
    MONTH_OCTOBER = _("October")
    MONTH_NOVEMBER = _("November")
    MONTH_DECEMBER = _("December")
    MONTH_CHOICES = (
        ("*", "*"),
        ('1', MONTH_JANUARY),
        ('2', MONTH_FEBRUARY),
        ('3', MONTH_MARCH),
        ('4', MONTH_APRIL),
        ('5', MONTH_MAY),
        ('6', MONTH_JUNE),
        ('7', MONTH_JULY),
        ('8', MONTH_AUGUST),
        ('9', MONTH_SEPTEMBER),
        ('10', MONTH_OCTOBER),
        ('11', MONTH_NOVEMBER),
        ('12', MONTH_DECEMBER),
    )

    # used in workflow Input validation
    MIN_SNAPSHOT_VALUE = 0
    MIN_BACKUP_VALUE = 0

    MAX_SNAPSHOT_VALUE = 100
    MAX_BACKUP_VALUE = 100

    BACKUP_TYPE_AUTO = 'auto'
    BACKUP_TYPE_FULL = 'full'
    BACKUP_TYPE_INCR = 'incr'
    BACKUP_TYPE_CHOICES = (
        (BACKUP_TYPE_AUTO, _("Auto")),
        (BACKUP_TYPE_FULL, _("Full")),
        (BACKUP_TYPE_INCR, _("Incr"))
    )

    BACKUP_CLONE_DEFAULT_NAME_PATTERN = "Clone of {}"


constants = ConstantsWrapper()