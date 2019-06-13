from unittest import TestCase, skip

from openstack_dashboard.dashboards.custom_backup.utils import cmp_dict


class UtilsTestCase(TestCase):

    def test_workflow_are_equal_case_1(self):
        self.assertTrue(cmp_dict({'a': 'a'}, {'a': 'a'}))

    def test_workflow_are_equal_case_2(self):
        self.assertFalse(cmp_dict({'a': 'b'}, {'a': 'a'}))

    def test_workflow_are_equal_case_3(self):
        self.assertFalse(cmp_dict({'a': {}}, {'a': 'a'}))

    def test_workflow_are_equal_case_4(self):
        self.assertTrue(cmp_dict({'a': {'c': 'c'}}, {'a': {'c': 'c'}}))

    def test_workflow_are_equal_case_5(self):
        self.assertTrue(cmp_dict(
            {'a': {'c': 'c'}, 1: 1},
            {'a': {'c': 'c'}, 1: 1})
        )

    def test_workflow_are_equal_case_6(self):
        self.assertFalse(cmp_dict(
            {'a': {'c': 'c'}, 1: 1},
            {'a': {'c': '1'}, 1: 1})
        )

    def test_workflow_are_equal_case_7(self):
        self.assertTrue(cmp_dict({}, {}))

    def test_workflow_are_equal_case_8(self):
        self.assertFalse(cmp_dict(
            {'a': {'b': '1'}, 1: 1},
            {'a': {'d': '1'}, 1: 1})
        )

    def test_workflow_are_equal_case_9(self):
        # same values, but keys differ
        self.assertFalse(cmp_dict(
            {'a': {'b': '1'}, 1: 1},
            {'a': {'d': '1'}, 1: 1})
        )

    def test_workflow_are_equal_case_10(self):
        self.assertFalse(cmp_dict(
            {u'only_backup': True,
             u'instance_stop': True,
             u'max_backups': 0,
             u'max_snapshots': 2,
             u'instance': u'4f21ce60-6925-4841-8855-5742be1fd49b',
             u'backup_type': u'auto',
             u'only_os': False,
             u'pattern': u'{0}_backup_{1}',
             u'instance_pause': False,
             u'cinder_backup': False,
             u'metadata': None},
            {'backup_type': u'auto',
             'instance_pause': False,
             'cinder_backup': False,
             'only_backup': True,
             'instance': u'43d345e0-fdfb-4639-8b78-cfcbc68846e0',
             'max_backups': 0,
             'instance_stop': False,
             'pattern': '{0}_backup_{1}',
             'only_os': False,
             'max_snapshots': 21,
             'metadata': None})
        )

    """
    The following three tests aim at verify that once the variable gets True, will hold this value until the end of loop
    this boolean logic is used inside che workflow[create|update] handle() methods  
    """
    def test_changed_data_boolean_circuit_case_1(self):
        v = False
        for y in [False, False, False, True]:
            v = v or y
        self.assertTrue(v)

    def test_changed_data_boolean_circuit_case_2(self):
        v = False
        for y in [True, False, False, False]:
            v = v or y
        self.assertTrue(v)

    def test_changed_data_boolean_circuit_case_3(self):
        v = True
        for y in [False, False, False]:
            v = v or y
        self.assertTrue(v)
