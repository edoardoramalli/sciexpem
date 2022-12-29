from rest_framework import serializers
from ExperimentManager.Models import WorkManager
import ExperimentManager.Serializers.Tool as Tool


class WorkManagerSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkManager
        fields = ['id', 'last_contact', 'computer', 'free_cores', 'num_cores', 'max_jobs', 'active_jobs']
        read_only_fields = ['id']


    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        self.user = kwargs.pop('user', None)
        req = ['last_contact', 'computer', 'free_cores', 'num_cores', 'max_jobs', 'active_jobs']

        if fields is None:
            fields = tuple(req)

        super(WorkManagerSerializer, self).__init__(*args, **kwargs)

        Tool.drop_fields(self, fields)