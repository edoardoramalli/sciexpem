from django.apps import AppConfig
import logging
from SciExpeM import settings
import os

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logger_handler = logging.FileHandler(os.path.join(settings.BASE_DIR, 'Files', 'CurveMatching.log'))
logger_handler.setFormatter(formatter)
logger_handler.setLevel(logging.INFO)


class CurvematchingConfig(AppConfig):
    name = 'CurveMatching'





