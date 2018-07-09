# -*- coding: utf-8 -*-
import json
import os

if os.environ.get('VCAP_SERVICES') is not None:
    vcap_services = json.loads(os.environ.get('VCAP_SERVICES'))
    os.environ['SECRET_KEY'] = vcap_services['user-provided'][0]['credentials']['SECRET_KEY']
    os.environ['MAPBOX_TOKEN'] = vcap_services['user-provided'][0]['credentials']['MAPBOX_TOKEN']

class Config(object):
    APP_ROOT = os.path.abspath(os.path.dirname(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_ROOT, os.pardir))
    SECRET_KEY = os.getenv('SECRET_KEY')
    MAPBOX_TOKEN = os.getenv('MAPBOX_TOKEN')

class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False


class TestConfig(Config):
    TESTING = True
