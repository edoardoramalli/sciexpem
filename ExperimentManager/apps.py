from django.apps import AppConfig
import logging
import os

from django.conf import settings


formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logger_handler = logging.FileHandler(filename=os.path.join(settings.BASE_DIR, 'Files', 'ExperimentManager.log'),
                                     mode="a")
logger_handler.setFormatter(formatter)
logger_handler.setLevel(logging.INFO)


class ExperimentManagerConfig(AppConfig):
    name = 'ExperimentManager'

    def ready(self):
        pass
