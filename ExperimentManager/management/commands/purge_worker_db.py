from django.core.management.base import BaseCommand, CommandError
from ExperimentManager.Models import WorkManager
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Delete objects older than 1 days'

    def handle(self, *args, **options):
        WorkManager.objects.filter(last_contact__lte=datetime.now()-timedelta(days=1)).delete()
        self.stdout.write('Deleted objects older than 1 days')