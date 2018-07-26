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

Currently this application is deployed to https://brownfield-sites-validator.cloudapps.digital on the [GOV.UK Paas](https://www.cloud.service.gov.uk/)

The following environment variables are needed for to run the application in production

    FLASK_ENV=production
    FLASK_CONFIG=config.Config
    FLASK_APP=application.wsgi:app
    SECRET_KEY=[something secret]
    MAPBOX_TOKEN=[set to valid token]

Deployment is done using a zero downtime deploy plugin [autopilot](https://github.com/contraband/autopilot)

Autopilot plugin provisions a new instance and then routes traffic to the new instance before tearing down the old one. Therefore
setting envionment variables via ```cf set-env``` is not an option (they variables would not be present in
the newly created instance).

To get around this issue, a standalone service ```user-provided-config-service``` has been created
to contain configuration. [See notes here](https://docs.cloudfoundry.org/devguide/services/user-provided.html). Any application that is bound to this service can
then access variables via the ```VCAP_SERVICES``` configuration values. See ```Config.py``` for
how those value are retrieved in the application. If you need to add configuration to the ```user-provided-config-service``` it
seems that updates are destructive, so please recreate all the values, do not just add the
new ones.


# Licence

The software in this project is open source and covered by [LICENSE](LICENSE) file.

All content and data in this repository is
[© Crown copyright](http://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/copyright-and-re-use/crown-copyright/)
and available under the terms of the [Open Government 3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) licence.
