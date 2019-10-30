# -*- coding: utf-8 -*-
import json
import os


class Config(object):
    APP_ROOT = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_ROOT, os.pardir))
    SECRET_KEY = os.getenv('SECRET_KEY')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    UPLOAD_FOLDER = '/tmp'


class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False
    DEBUG_TB_ENABLED = False
    DEBUG_TB_PROFILER_ENABLED = DEBUG_TB_ENABLED if DEBUG_TB_ENABLED else False


class TestConfig(Config):
    TESTING = True
