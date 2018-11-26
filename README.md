# Prototype Brownfield sites validator

This prototype is being used to explore approaches to validating geospatial data publications, starting with the [brownfield site register standard](https://www.gov.uk/government/publications/brownfield-land-registers-data-standard).

The work here builds upon existing tools and services, such as [csvlint.io](http://csvlint.io/) from the ODI and 
the [LGA validator](https://validator.opendata.esd.org.uk/) though reporting issues found in .xls, .xlsx .xlsm and other file formats,
checking headers and co-constraints,
and with a stronger focus on geospatial issues.

The tool may be used to fix common errors, view the register on a map, and convert the data to [geojson](https://en.wikipedia.org/wiki/GeoJSON) and other formats.

Requirements

- [Python 3](https://www.python.org/)
- [Node](https://nodejs.org/en/) and [Npm](https://www.npmjs.com/)

Getting started
---------------

Install front end build tool (gulp)

    npm install && gulp scss

Make a virtualenv for the project and install python dependencies

    pip install -r requirements.txt

Create a local postgres database for the application called **brownfield** (see the .flaskenv file)

    createdb brownfield
    
Install PostGIS

If you're using Postgres.app on OSX it should be installed already but you'll need to add it to the brownfield db. Using `psql -d brownfield`, run:

    CREATE EXTENSION postgis;

Check if all went well

    SELECT PostGIS_Version();

You should see something similar to:

    2.4 USE_GEOS=1 USE_PROJ=1 USE_STATS=1

Run database migrations

    python -m flask db upgrade

Load data

        python -m flask load

Run the application

    python -m flask run

Note you can add and commit public environment variables to .flaskenv, do not add anything secret to this
file. Secret configuration variables should be added to a .env file in base directory of the project.

Deployment
----------

Currently this application is deployed to brownfield-sites-validator.herokuapp.com. The heroku app is configured to deploy on commits
to master.

The following environment variables are needed for to run the application on heroku

    FLASK_ENV=production
    FLASK_CONFIG=config.Config
    FLASK_APP=application.wsgi:app
    SECRET_KEY=[something secret]
    MAPBOX_TOKEN=[set to valid token]
    S3_REGION=eu-west-1
    S3_BUCKET=digital-land-output


Useful commands
---------------

Use the following to copy all GOVUK design system components to templates folder. You'll need to be in `src/govuk-frontend` dir.

    find . -name '*.njk' | cpio -pdm ../../application/templates/

# Licence

The software in this project is open source and covered by [LICENSE](LICENSE) file.

All content and data in this repository is
[© Crown copyright](http://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/copyright-and-re-use/crown-copyright/)
and available under the terms of the [Open Government 3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) licence.
