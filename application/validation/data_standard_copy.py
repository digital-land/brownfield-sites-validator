column_name_to_markdown = {
    'OwnershipStatus':
        '''
        This should indicate site’s ownership by entering one of the following values:
            * owned by a public authority
            * not owned by a public authority
            * mixed ownership

        For more information see paragraph 5 of [Schedule 2 of the 2017 Regulations](http://www.legislation.gov.uk/uksi/2017/403/schedule/2/made).
        ''',

    'PlanningStatus':
        '''
        This should indicate what stage of the planning process the site is at:
            * permissioned
            * not permissioned
            * pending decision
        When part of a site is permissioned, it should be recorded as “permissioned” and you should explain in the ‘Notes’ field why it’s only partly permissioned.
        
        For more information see paragraph 5 of [Schedule 2 of the 2017 Regulations](http://www.legislation.gov.uk/uksi/2017/403/schedule/2/made).
        ''',
    'PermissionType':
    '''
        Choose one of the following to indicate what permission type the site has:
            * full planning permission
            * outline planning permission
            * reserved matters approval
            * permission in principle
            * technical details consent
            * planning permission granted under an order
            * other
    '''
}