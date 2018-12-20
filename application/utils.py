ordered_brownfield_register_fields = ['OrganisationURI',
                                      'OrganisationLabel',
                                      'SiteReference',
                                      'PreviouslyPartOf',
                                      'SiteNameAddress',
                                      'SiteplanURL',
                                      'CoordinateReferenceSystem',
                                      'GeoX',
                                      'GeoY',
                                      'Hectares',
                                      'OwnershipStatus',
                                      'Deliverable',
                                      'PlanningStatus',
                                      'PermissionType',
                                      'PermissionDate',
                                      'PlanningHistory',
                                      'ProposedForPIP',
                                      'MinNetDwellings',
                                      'DevelopmentDescription',
                                      'NonHousingDevelopment',
                                      'Part2',
                                      'NetDwellingsRangeFrom',
                                      'NetDwellingsRangeTo',
                                      'HazardousSubstances',
                                      'SiteInformation',
                                      'Notes',
                                      'FirstAddedDate',
                                      'LastUpdatedDate']


def to_boolean(value):
    if value is None:
        return False
    if str(value).lower() in ['1', 't', 'true', 'y', 'yes', 'on']:
        return True
    return False