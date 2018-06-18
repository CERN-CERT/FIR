import logging
import ldap
import six

from fir_userinteraction.constants import DEFAULT_LDAP_QUERY_FIELDS, LDAP_USER_SEARCH, LDAP_GROUP_SEARCH
from fir_userinteraction.helpers import get_django_setting_or_default


class LdapConnection:

    def __init__(self):
        self.ldap_server = get_django_setting_or_default('LDAP_SERVER', '')
        self.user_query_base = get_django_setting_or_default('LDAP_USER_QUERY_BASE', 'users')
        self.group_query_base = get_django_setting_or_default('LDAP_GROUP_QUERY_BASE', 'groups')

        try:
            self.con = ldap.initialize(self.ldap_server)
        except Exception as e:
            logging.error('An exception has occured while initializing LDAP: {}'.format(e))

    @classmethod
    def ldap_enabled(cls):
        return get_django_setting_or_default('LDAP_ENABLED', False)

    def query_type_to_query_base(self, query_type):
        """
        Return the query base depending on the query type
        @param query_type: a string that is either 'user' or 'group'
        @return: the query base string; if the query_type was unknown, it returns None
        """
        if query_type == LDAP_USER_SEARCH:
            return self.user_query_base
        elif query_type == LDAP_GROUP_SEARCH:
            return self.group_query_base
        else:
            logging.error('Could not find query base: {}'.format(query_type))
            return None

    def search_in_ldap(self, cn, query_type=LDAP_USER_SEARCH,
                       query_fields=DEFAULT_LDAP_QUERY_FIELDS):
        """
        Searches based on cn, mail or sn in LDAP, returning all of the results found.
        @param cn: String representing the entity to be found in LDAP
        @param query_type: String representing the query type, currently only user and group are supported
        @param query_fields: List of strings representing the fields to extract from the query
        @return: a list of LDAP entities
        """
        dn = self.query_type_to_query_base(query_type)
        search_results = []
        try:
            search_results = self.con.search_s(dn, ldap.SCOPE_SUBTREE,
                                               '(cn={0})'.format(cn),
                                               query_fields
                                               )
        except Exception as e:
            logging.error('An exception has occured while querying LDAP: {}'.format(e))
        raw_results = [data_dict for _, data_dict in search_results]
        return [{k: v[0] if v else None for k, v in six.iteritems(i)} for i in raw_results]

    @classmethod
    def check_enabled_account(cls, ldap_entity):
        if 'userAccountControl' in ldap_entity:
            return int(ldap_entity['userAccountControl']) & 2 == 0
        return True
