from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied


def user_in_group(group_name):
    def in_groups(u):
        if u.is_authenticated:
            if u.is_superuser | u.groups.filter(name=group_name).exists():
                return True
        raise PermissionDenied
    return user_passes_test(in_groups)
