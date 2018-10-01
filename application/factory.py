# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template
from flask.cli import load_dotenv

if os.environ['FLASK_ENV'] == 'production':
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path)


def create_app(config_filename):
    app = Flask(__name__)
    app.config.from_object(config_filename)
    register_errorhandlers(app)
    register_blueprints(app)
    register_extensions(app)
    register_commands(app)
    register_filters(app)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 10
    return app


def register_errorhandlers(app):
    def render_error(error):
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return render_template("error/{0}.html".format(error_code)), error_code
    for errcode in [400, 401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_blueprints(app):
    from application.frontend.views import frontend
    app.register_blueprint(frontend)


def register_extensions(app):

    from application.extensions import db
    db.init_app(app)

    from application.models import BrownfieldSitePublication
    from application.extensions import migrate
    migrate.init_app(app=app)


def register_commands(app):
    from application.commands import load, validate, clear
    app.cli.add_command(load, name='load')
    app.cli.add_command(validate, name='validate')
    app.cli.add_command(clear, name='clear')


def register_filters(app):
    from application.filters import format_error, format_warning, healthcheck, format_date_time
    app.add_template_filter(format_error)
    app.add_template_filter(format_warning)
    app.add_template_filter(healthcheck)
    app.add_template_filter(format_date_time)

