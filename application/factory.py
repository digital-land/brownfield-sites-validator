# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template
from flask.cli import load_dotenv
from jinja2 import PackageLoader, PrefixLoader, ChoiceLoader


if os.environ.get('FLASK_ENV') == 'production':
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path)


def create_app(config_filename):

    if os.environ.get('SENTRY_DSN') is not None:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        sentry_sdk.init(
            dsn=os.environ.get('SENTRY_DSN'),
            integrations=[FlaskIntegration()]
        )

    app = Flask(__name__)
    app.config.from_object(config_filename)
    register_errorhandlers(app)
    register_blueprints(app)
    register_extensions(app)
    register_commands(app)
    register_filters(app)
    register_templates(app)
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
    from application.extensions import misaka
    from application.extensions import db
    from application.extensions import migrate

    misaka.init_app(app)
    db.init_app(app)
    migrate.init_app(app)

    if os.environ.get('FLASK_ENV') == 'production':
        from flask_sslify import SSLify
        SSLify(app)


def register_commands(app):
    pass


def register_filters(app):
    from application.filters import healthcheck, pluralise,\
        format_date_time, count_fields_with_errors, count_fields_with_warnings,\
        check_if_fixable
    app.add_template_filter(healthcheck)
    app.add_template_filter(pluralise)
    app.add_template_filter(format_date_time)
    app.add_template_filter(count_fields_with_errors)
    app.add_template_filter(count_fields_with_warnings)
    app.add_template_filter(check_if_fixable)


def register_templates(app):
    multi_loader = ChoiceLoader([
        app.jinja_loader,
        PrefixLoader({
            'govuk-jinja-components': PackageLoader('govuk-jinja-components')
        })
    ])
    app.jinja_loader = multi_loader

