# Prototype Brownfield sites validator

This prototype is being used to explore approaches to working with brownfield site. The work here is intended to complement existing tools/services.

Check a publication meets the [brownfield site register standard](https://www.gov.uk/government/publications/brownfield-land-registers-data-standard).

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

Run the application

    python -m flask run

Note you can add and commit public environment variables to .flaskenv, do not add anything secret to this
file. Secret configuration variables should be added to a .env file in base directory of the project.

Deployment
----------

Currently this application is deployed to https://brownfield-sites-validator.cloudapps.digital on the [GOV.UK Paas](https://www.cloud.service.gov.uk/)

The following environment variables are set using ```cf set-env```

    FLASK_ENV=production
    FLASK_CONFIG=config.Config
    FLASK_APP=application.wsgi:app
    SECRET_KEY=[something secret]
    MAPBOX_TOKEN=[set to valid token]

# Licence

The software in this project is open source and covered by [LICENSE](LICENSE) file.

All content and data in this repository is
[© Crown copyright](http://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/copyright-and-re-use/crown-copyright/)
and available under the terms of the [Open Government 3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) licence.
