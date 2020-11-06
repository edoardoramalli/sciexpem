from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Set Permissions to groups'

    def handle(self, *args, **options):
        # can_fm_list = Permission.objects.get(name='can_fm_list')
        permissions = set()

        # We create (but not persist) a temporary superuser and use it to game the
        # system and pull all permissions easily.
        tmp_superuser = get_user_model()(
            is_active=True,
            is_superuser=True
        )

        # We go over each AUTHENTICATION_BACKEND and try to fetch
        # a list of permissions
        for backend in auth.get_backends():
            if hasattr(backend, "get_all_permissions"):
                permissions.update(backend.get_all_permissions(tmp_superuser))

        read = Permission.objects.filter(codename__contains="view_", content_type__app_label="ExperimentManager")
        write = Permission.objects.filter(codename__contains="add_", content_type__app_label="ExperimentManager")
        cancel = Permission.objects.filter(codename__contains="delete_", content_type__app_label="ExperimentManager")
        update = Permission.objects.filter(codename__contains="change_", content_type__app_label="ExperimentManager")
        execute = Permission.objects.filter(codename__contains="execute_")

        read_group = Group.objects.get(name="READ")
        write_group = Group.objects.get(name="WRITE")
        cancel_group = Group.objects.get(name="DELETE")
        update_group = Group.objects.get(name="UPDATE")
        execute_group = Group.objects.get(name="EXECUTE")

        for r in read:
            read_group.permissions.add(r)

        for w in write:
            write_group.permissions.add(w)

        for c in cancel:
            cancel_group.permissions.add(c)

        for u in update:
            update_group.permissions.add(u)

        for e in execute:
            execute_group.permissions.add(e)
