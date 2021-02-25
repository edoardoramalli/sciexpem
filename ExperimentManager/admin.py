from django.contrib import admin
from django_cron import CronJobBase, Schedule
from django.core import management
# Register your models here.


class Backup(CronJobBase):
    RUN_EVERY_MINS = 60*24*5
    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ExperimentManager.Backup'

    def do(self):
        management.call_command('dbbackup')
