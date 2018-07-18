from vladiate import Vlad
from vladiate.exceptions import ValidationException
from vladiate.validators import Validator, SetValidator, FloatValidator, IntValidator, Ignore


class ValidatorWarning:

    def __init__(self, name, message):
        self.name = name
        self.message = message


class URLValidator(Validator):

    def __init__(self, **kwargs):
        super(URLValidator, self).__init__(**kwargs)
        self.failures = set([])

    def validate(self, field, row={}):
        if not self.empty_ok:
            valid, exception = self.validate_url(field)
            if not valid and (field or not self.empty_ok):
                self.failures.add(field)
                raise ValidationException("{} - {}".format(field, exception))

    @property
    def bad(self):
        return self.failures

    @staticmethod
    def validate_url(url):
        from urllib.request import urlopen
        from urllib.error import URLError, HTTPError
        try:
            urlopen(url)
            return True, None
        except HTTPError as e:
            return False, e
        except URLError as e:
            return False, e.reason
        except Exception as e:
            return False, e


class StringNoLineBreaksValidator(Validator):

    def __init__(self, **kwargs):
        super(StringNoLineBreaksValidator, self).__init__(**kwargs)
        self.failures = set([])

    def validate(self, field, row={}):
        if not self.empty_ok:
            valid = self.has_no_linebreaks(field)
            if not valid and (field or not self.empty_ok):
                self.failures.add(field)
                raise ValidationException("{} - contains line breaks".format(field))

    @property
    def bad(self):
        return self.failures

    @staticmethod
    def has_no_linebreaks(field):
        if '\r\n' in field or '\n' in field:
            return False
        return True


class ISO8601DateValidator(Validator):

    def __init__(self, **kwargs):
        super(ISO8601DateValidator, self).__init__(**kwargs)
        self.failures = set([])

    def validate(self, field, row={}):
        if not self.empty_ok:
            valid, message = self.validate_date(field)
            if not valid and (field or not self.empty_ok):
                self.failures.add(field)
                raise ValidationException("{} - {}".format(field, message))

    @property
    def bad(self):
        return self.failures

    @staticmethod
    def validate_date(field):
        import datetime
        try:
            datetime.datetime.strptime(field, '%Y-%m-%d')
            return True, None
        except ValueError as e:
            return False, 'incorrect date format - should be YYYY-MM-DD'


class BrownfieldSiteRegisterValidator(Vlad):

    valid_coordinate_reference_system = ['WGS84', 'OSGB36', 'ETRS89']
    valid_ownership_status = ['owned by a public authority', 'not owned by a public authority', 'unknown ownership',
                              'mixed ownership']
    valid_planning_status = ['permissioned', 'not permissioned', 'pending decision']
    valid_permission_type = ['full planning permission',
                             'outline planning permission',
                             'reserved matters approval',
                             'permission in principle',
                             'technical details consent',
                             'planning permission granted under an order',
                             'other']

    validators = {
        'OrganisationURI' : [
            URLValidator()
        ],
        'OrganisationLabel' : [
            StringNoLineBreaksValidator()
        ],
        'SiteReference': [
            StringNoLineBreaksValidator()
        ],
        'PreviouslyPartOf': [
            StringNoLineBreaksValidator(empty_ok=True)
        ],
        'SiteNameAddress': [
            StringNoLineBreaksValidator()
        ],
        'SiteplanURL': [
            URLValidator()
        ],
        'CoordinateReferenceSystem': [
            SetValidator(valid_set=valid_coordinate_reference_system)
        ],
        'GeoX': [
            FloatValidator()
        ],
        'GeoY': [
            FloatValidator()
        ],
        'Hectares': [
            FloatValidator()
        ],
        'OwnershipStatus': [
            SetValidator(valid_set=valid_ownership_status)
        ],
        'Deliverable': [
            SetValidator(valid_set=['yes'], empty_ok=True)
        ],
        'PlanningStatus': [
            SetValidator(valid_set=valid_planning_status)
        ],
        'PermissionType': [
            SetValidator(valid_set=valid_permission_type, empty_ok=True)
        ],
        'PermissionDate': [
            ISO8601DateValidator(empty_ok=True)
        ],
        'PlanningHistory': [
            URLValidator(empty_ok=True)
        ],
        'ProposedForPIP': [
            SetValidator(valid_set=['yes'], empty_ok=True)
        ],
        'MinNetDwellings': [
            IntValidator()
        ],
        'DevelopmentDescription': [
            Ignore()
        ],
        'NonHousingDevelopment': [
            Ignore()
        ],
        'Part2': [
            SetValidator(valid_set=['yes'], empty_ok=True)
        ],
        'NetDwellingsRangeFrom': [
            IntValidator(empty_ok=True)
        ],
        'NetDwellingsRangeTo': [
            IntValidator(empty_ok=True)
        ],
        'HazardousSubstances': [
            SetValidator(valid_set=['yes'], empty_ok=True)
        ],
        'SiteInformation': [
            URLValidator(empty_ok=True)
        ],
        'Notes': [
            Ignore()
        ],
        'FirstAddedDate': [
            ISO8601DateValidator()
        ],
        'LastUpdatedDate': [
            ISO8601DateValidator()
        ]
    }