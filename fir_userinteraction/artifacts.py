from fir_artifacts.artifacts import AbstractArtifact

import re

WHITESPACE_CHAR = u'\u200b'


class DeviceName(AbstractArtifact):
    case_sensitive = False
    key = 'device'
    display_name = 'Devices'

    regex = re.compile(u'(?P<search>{0}[^\s]+{0})'.format(WHITESPACE_CHAR), re.UNICODE)

    @classmethod
    def find(cls, data):
        results = []
        for i in re.finditer(cls.regex, data):
            group_str = i.group('search').lower()
            results.append(group_str.replace(WHITESPACE_CHAR, ''))
        return results
