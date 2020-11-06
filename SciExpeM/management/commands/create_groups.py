# from django.contrib.auth.models import Group
# # TODO add permission to group --> magari con script esterno
# for group in GROUPS:
#     new_group, created = Group.objects.get_or_create(name=group)

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Create groups'
    GROUPS = ['READ', 'WRITE', 'DELETE', 'UPDATE', 'EXECUTE']

    def handle(self, *args, **options):
        for group in self.GROUPS:
            new_group, created = Group.objects.get_or_create(name=group)