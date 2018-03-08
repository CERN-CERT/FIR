from django.test import TestCase

from artifacts import DeviceName, WHITESPACE_CHAR


# Create your tests here.
class DeviceNameArtifactTest(TestCase):

    def test_single_device_matches(self):
        test_str = u'{0}cristi-pc{0}'.format(WHITESPACE_CHAR)
        expected = test_str.replace(WHITESPACE_CHAR, '')
        data = u'The device affected is {expected}. Please take appropriate action.'.format(expected=test_str)

        results = DeviceName.find(data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], expected)

    def test_multiple_device_matches(self):
        test_str = u'{0}cristi-pc{0}'.format(WHITESPACE_CHAR)
        expected = test_str.replace(WHITESPACE_CHAR, '')
        data = u'The device affected is {expected1}. Please take appropriate action for {expected2}.' \
            .format(expected1=test_str, expected2=test_str)

        results = DeviceName.find(data)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], expected)
        self.assertEqual(results[1], expected)

    def test_no_device_match(self):
        data = 'The device is cristi-pc'
        results = DeviceName.find(data)

        self.assertEqual(len(results), 0)
