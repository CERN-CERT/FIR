"""
Auth function for use with the SSO interface


"""
import operator

from django.contrib.auth.models import Group
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

import incidents
from incidents.models import Profile, AccessControlEntry, BusinessLine

GROUPS_BL_NAME = 'Groups'

INCIDENT_VIEWERS_ROLE = 'Incident viewers'
USERS_BL = 'Users'


def user_creation_function(request, user):
    try:
        Profile.objects.get(user=user)
    except ObjectDoesNotExist:
        profile = Profile()
        profile.user = user
        profile.hide_closed = False
        profile.incident_number = 50
        profile.save()
    user.save()
    return user


def get_or_create_user_bl(username):
    try:
        users_bl = BusinessLine.objects.get(Q(name=USERS_BL) & Q(depth=1))
    except ObjectDoesNotExist:
        users_bl = BusinessLine.add_root(name=USERS_BL)
        users_bl.save()

    users_bl = BusinessLine.objects.get(Q(name=USERS_BL) & Q(depth=1))
    current_user_bls = BusinessLine.objects.filter(name=username)
    if not current_user_bls:
        bl = users_bl.add_child(name=username)
        return bl
    for bl in current_user_bls:
        if bl.depth == 2:
            return bl


def get_or_create_groups_bl():
    try:
        return BusinessLine.objects.get(name=GROUPS_BL_NAME, depth=1)
    except ObjectDoesNotExist:
        return BusinessLine.add_root(name=GROUPS_BL_NAME)


def group_extraction_fct(request, user, group_json):
    incident_viewers_role = Group.objects.get_by_natural_key(INCIDENT_VIEWERS_ROLE)
    user_acls = user.accesscontrolentry_set.all()
    ldap_group_names = group_json['groups']
    # get all the groups from ldap
    # remove any user permissions that don't belong to him anymore and add all the others

    user_bl = get_or_create_user_bl(user.username)
    groups_bl = get_or_create_groups_bl()
    to_add_ace = [user_bl]

    print('User bl: {}'.format(user_bl))

    user_bl_acl = user_acls.filter(business_line__name=user.username)
    if not user_bl_acl:
        AccessControlEntry.objects.create(user=user, role=incident_viewers_role, business_line=user_bl)
    for ldap_group in ldap_group_names:
        existing_permission = user_acls.filter(business_line__name=ldap_group)
        if not existing_permission:
            child_bl = groups_bl.add_child(name=ldap_group)
            ace = AccessControlEntry.objects.create(user=user, role=incident_viewers_role, business_line=child_bl)
            print('Created ace: {}'.format(ace))

    user.save()

    to_remove_filter = reduce(operator.and_, (~Q(business_line__name=x) for x in ldap_group_names))
    to_remove_acls = user_acls.filter(to_remove_filter)
    for acl in to_remove_acls:
        acl.delete()

    return ldap_group_names


def init_session(request):
    incidents.views.init_session(request)
