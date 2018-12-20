# -*- coding: utf-8 -*-
import json
import os


class Config(object):
    APP_ROOT = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_ROOT, os.pardir))
    SECRET_KEY = os.getenv('SECRET_KEY')
    MAPBOX_TOKEN = os.getenv('MAPBOX_TOKEN')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    S3_REGION = os.getenv('S3_REGION')
    S3_BUCKET = os.getenv('S3_BUCKET')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    UPLOAD_FOLDER = '/tmp'
    GH_TOKEN = os.getenv('GH_TOKEN')

class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False
    DEBUG_TB_ENABLED = False
    DEBUG_TB_PROFILER_ENABLED = DEBUG_TB_ENABLED if DEBUG_TB_ENABLED else False


class TestConfig(Config):
    TESTING = True
