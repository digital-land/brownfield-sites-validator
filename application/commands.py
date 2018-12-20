import csv
import datetime
import json
import os
import shutil
from contextlib import closing
from pathlib import Path
from urllib.request import urlopen

import htmlmin
import ijson
from flask import current_app, url_for
from git import Repo
from ijson import common

import boto3
import click
import frontmatter
import requests
from flask.cli import with_appcontext
from sqlalchemy import asc
from sqlalchemy.orm.exc import NoResultFound

from application.extensions import db
from application.frontend.views import get_data_and_validate
from application.models import BrownfieldSiteRegister

json_to_geo_query = "SELECT ST_SetSRID(ST_GeomFromGeoJSON('%s'), 4326);"


def floaten(event):
    if event[1] == 'number':
        return (event[0], event[1], float(event[2]))
    else:
        return event


@click.command()
@with_appcontext
def load():

    from flask import current_app
    from application.extensions import db

    s3_region = current_app.config['S3_REGION']
    s3_bucket = current_app.config['S3_BUCKET']
    s3_bucket_url = 'http://%s.s3.amazonaws.com' % s3_bucket

    s3 = boto3.resource('s3', region_name=s3_region)
    bucket = s3.Bucket(s3_bucket)

    org_feature_mappings = {}

    item_url = '%s/organisation.tsv' % s3_bucket_url
    print('Loading', item_url)
    with closing(requests.get(item_url, stream=True)) as r:
        reader = csv.DictReader(r.iter_lines(decode_unicode=True), delimiter='\t')
        for row in reader:
            org = row['organisation']
            if 'local-authority' in org or 'national-park' in org:
                if not db.session.query(BrownfieldSiteRegister).get(org):
                    register = BrownfieldSiteRegister(organisation=org,
                                                      name=row['name'],
                                                      website=row['website'])
                    db.session.add(register)
                    db.session.commit()

                    if row.get('feature') is not None:
                        org_feature_mappings[row.get('feature')] = org

    features_url = '%s/feature/local-authority-districts.geojson' % s3_bucket_url
    load_features(features_url, org_feature_mappings)

    features_url = '%s/feature/national-park-boundary.geojson' % s3_bucket_url
    load_features(features_url, org_feature_mappings)
    db.session.execute('CLUSTER brownfield_site_register USING idx_brownfield_site_register_geometry')

    urls = ['%s/%s' % (s3_bucket_url, file.key) for file in bucket.objects.filter(Prefix='publication/brownfield-sites')]

    for url in urls:

        try:
            content = requests.get(url).content.decode('utf-8')
            c = frontmatter.loads(content)
            publication = c.metadata['publication']
            register = c.metadata['organisation']
            copyright = c.metadata['copyright']
            licence = c.metadata['licence']
            data_url = c.metadata['data-url']
            suffix = c.metadata.get('suffix')

            geojson_url = '%s/feature/%s.geojson' % (s3_bucket_url, publication)
            geojson = requests.get(geojson_url).json()

            try:
                register = BrownfieldSiteRegister.query.get(register)
                register.register_url = data_url
                register.publication_copyright = copyright
                register.publication_licence = licence
                register.publication = publication
                register.publication_suffix = suffix
                register.register_geojson = geojson

                db.session.add(register)
                db.session.commit()

            except Exception as e:
                print('Error saving site for', register)

        except Exception as e:
            print('Error loading', url, e)

    print('Done')


@click.command()
@with_appcontext
def validate():
    registers = BrownfieldSiteRegister.query.all()
    for register in registers:
        try:
            if register.register_url is not None:
                print('Validating', register.register_url)
                get_data_and_validate(register, register.register_url)
                print('Added data from',  register.register_url)
        except Exception as e:
            print('error', e)
    print('Done')


def load_features(features_url, org_feature_mappings):

    print('Loading', features_url)

    try:
        if features_url.startswith('http'):
            f = urlopen(features_url)
        else:
            f = open(features_url, 'rb')
        events = map(floaten, ijson.parse(f))
        data = common.items(events, 'features.item')

        for feature in data:
            id = feature['properties'].get('feature')
            item = 'item:%s' % feature['properties'].get('item')
            feature_id = id if id is not None else item
            try:
                register = BrownfieldSiteRegister.query.get(org_feature_mappings[feature_id])
                geojson = json.dumps(feature['geometry'])
                register.geometry = db.session.execute(json_to_geo_query % geojson).fetchone()[0]
                register.geojson = feature['geometry']
                db.session.add(register)
                db.session.commit()
            except KeyError as e:
                print('No organisation for feature', feature_id)
            except Exception as e:
                print(e)

    except Exception as e:
        print(e)
        print('Error loading', features_url)
    finally:
        try:
            f.close()
        except:
            pass


@click.command()
@with_appcontext
def clear():
    db.session.query(BrownfieldSiteRegister).delete()
    db.session.commit()
    print('cleared db')


@click.command()
@with_appcontext
def update_brownfield_urls():
    path = Path(os.path.dirname(os.path.realpath(__file__))).parent
    update_file_path = os.path.join(path, 'data', 'updates.csv')
    with open(update_file_path) as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                register = BrownfieldSiteRegister.query.filter_by(publication=row['brownfield_register_publication']).one()
                register.brownfield_register_url = row['brownfield_register_url']
                db.session.add(register)
                db.session.commit()
                print('Updated:', row['brownfield_register_publication'], 'to', row['brownfield_register_url'])
            except NoResultFound as e:
                print('Found no publication for:', row['brownfield_register_publication'])


@click.command()
@with_appcontext
def build_report():

    @current_app.context_processor
    def static_path():
        return {'static_path': '/brownfield-sites'}

    current_dir = Path(os.path.dirname(os.path.realpath(__file__)))
    build_dir = os.path.join(current_dir.parent, 'build')
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
    else:
        shutil.rmtree(build_dir)

    os.chdir(build_dir)

    remote_url = 'https://%s@github.com/digital-land/brownfield-sites.git' % current_app.config['GH_TOKEN']
    repo = Repo.clone_from(remote_url, build_dir)

    with current_app.test_client() as client:
        resp = client.get('/results')
        html = resp.data.decode('utf-8')
        # output = htmlmin.minify(html)
        output = html

    if not os.path.exists(build_dir):
        os.makedirs(build_dir)

    docs_dir = os.path.join(build_dir, 'docs')

    results_dir = os.path.join(docs_dir, 'results')
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)

    outfile = os.path.join(build_dir, results_dir, 'index.html')
    with open(outfile, 'w') as f:
        f.write(output)

    repo.index.add([outfile])

    with current_app.test_client() as client:
        resp = client.get('/results/map')
        html = resp.data.decode('utf-8')
        output = htmlmin.minify(html)

    map_dir = os.path.join(results_dir, 'map')
    if not os.path.exists(map_dir):
        os.makedirs(map_dir)

    outfile = os.path.join(map_dir, 'index.html')
    with open(outfile, 'w') as f:
        f.write(output)

    repo.index.add([outfile])

    registers = db.session.query(BrownfieldSiteRegister.organisation).order_by(
            asc(BrownfieldSiteRegister.name)).all()
    for r in registers:
        with current_app.test_client() as client:
            url = '/results/%s/' % r.organisation
            resp = client.get(url)
            if resp.status_code == 200:
                html = resp.data.decode('utf-8')
                output = htmlmin.minify(html)
                la_dir = os.path.join(results_dir, r.organisation.replace(':', '-'))
                if not os.path.exists(la_dir):
                    os.makedirs(la_dir)
                outfile = os.path.join(la_dir, 'index.html')
                with open(outfile, 'w') as f:
                    f.write(output)
                repo.index.add([outfile])

    static_src = os.path.join(current_dir, 'static')
    static_dest = os.path.join(docs_dir, 'static')
    if os.path.exists(static_dest):
        shutil.rmtree(static_dest)

    shutil.copytree(static_src, static_dest)

    repo.index.add([static_dest])
    message = 'Updated %s' % datetime.datetime.utcnow().isoformat()
    repo.index.commit(message)
    repo.remotes.origin.push()

    shutil.rmtree(build_dir)
