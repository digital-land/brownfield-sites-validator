import json

from flask import Blueprint, request, render_template, abort
from sqlalchemy import asc, func

from application.extensions import db
from application.models import BrownfieldSiteRegister
from application.utils import to_boolean

brownfield_validation = Blueprint('brownfield_validation', __name__, template_folder='templates', url_prefix='/brownfield-sites')


@brownfield_validation.route('/results')
def validate_results():

    static_mode = to_boolean(request.args.get('static_mode', False))

    registers = db.session.query(BrownfieldSiteRegister.organisation,
                                 BrownfieldSiteRegister.name,
                                 BrownfieldSiteRegister.validation_result,
                                 BrownfieldSiteRegister.validation_created_date,
                                 BrownfieldSiteRegister.validation_updated_date
                                 ).order_by(
        asc(BrownfieldSiteRegister.name)).all()
    return render_template('results.html', registers=registers, static_mode=static_mode)


@brownfield_validation.route('/results/map')
def all_results_map():

    static_mode = to_boolean(request.args.get('static_mode', False))

    return render_template('results-map.html', resultdata=get_all_boundaries_and_results(static_mode=static_mode), static_mode=static_mode)



@brownfield_validation.route('/results/<local_authority>/')
def static_validate(local_authority):

    static_mode = to_boolean(request.args.get('static_mode', False))

    register = BrownfieldSiteRegister.query.get(local_authority)

    if register.validation_result:

        context = {'url': register.register_url,
                   'result': register.validation_result,
                   'register': register,
                   'static_mode': static_mode
                   }
        if register.validation_result is not None:
            context['feature'] = register.validation_geojson()

        return render_template('result.html', **context)

    else:
        abort(404)


def get_all_boundaries_and_results(static_mode=False):
    registers = db.session.query(BrownfieldSiteRegister.organisation,
                                 BrownfieldSiteRegister.name,
                                 func.ST_AsGeoJSON(func.ST_SimplifyVW(BrownfieldSiteRegister.geometry, 0.00001)).label('geojson'),
                                 BrownfieldSiteRegister.validation_result,
                                 BrownfieldSiteRegister.register_url,
                                 BrownfieldSiteRegister.validation_created_date,
                                 BrownfieldSiteRegister.validation_updated_date).all()
    data = []
    for reg in registers:
        data.append(get_boundary_and_result(reg, static_mode=static_mode))
    return data


def get_boundary_and_result(register, static_mode=False):
    package = {}
    package['org_id'] = register.organisation if not static_mode else register.organisation.replace(':', '-')
    package['org_name'] = register.name
    if register.geojson:
        package['feature'] = json.loads(register.geojson)
    if register.validation_result:
        package['csv_url'] = register.register_url
        package['results'] = register.validation_result
    else:
        package['results'] = "No results available"

    return package

