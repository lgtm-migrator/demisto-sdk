data = {
    'Expanse': {
        'packsDependentOnThisPackMandatorily': {},
        'path': 'Packs/Expanse',
        'fullPath': '/Users/rshalem/dev/demisto/content/Packs/Expanse',
    },
    'ExpanseV2': {
        'packsDependentOnThisPackMandatorily': {
            'X509Certificate': {
                'mandatory': True,
                'dependent_items': [
                    (
                        ('indicator_field', 'indicator_expansetags'),
                        [('layout', 'certificate')],
                    )
                ],
            },
            'CVE_2021_44228': {
                'mandatory': True,
                'dependent_items': [
                    (
                        ('integration', 'ExpanseV2'),
                        [('playbook', 'CVE-2021-44228 - Log4j RCE')],
                    )
                ],
            },
        },
        'path': 'Packs/ExpanseV2',
        'fullPath': '/Users/rshalem/dev/demisto/content/Packs/ExpanseV2',
    },
    'Traps': {
        'packsDependentOnThisPackMandatorily': {
            'PANWComprehensiveInvestigation': {
                'mandatory': True,
                'dependent_items': [
                    (
                        ('integration', 'Traps'),
                        [
                            (
                                'playbook',
                                'Palo Alto Networks - Endpoint Malware Investigation',
                            )
                        ],
                    ),
                    (
                        ('incident_field', 'incident_trapsid'),
                        [('layout', 'PANW Endpoint Malware')],
                    ),
                ],
            }
        },
        'path': 'Packs/Traps',
        'fullPath': '/Users/rshalem/dev/demisto/content/Packs/Traps',
    },
    'CortexXDR': {
        'packsDependentOnThisPackMandatorily': {
            'PANWComprehensiveInvestigation': {
                'mandatory': True,
                'dependent_items': [
                    (
                        ('incident_field', 'incident_xdrresolvecomment'),
                        [('layout', 'PANW Endpoint Malware')],
                    )
                ],
            },
            'PortScan': {
                'mandatory': True,
                'dependent_items': [
                    (
                        ('integration', 'Cortex XDR - IR'),
                        [('playbook', 'Port Scan - Internal Source')],
                    )
                ],
            },
            'CommonPlaybooks': {
                'mandatory': True,
                'dependent_items': [
                    (
                        ('playbook', 'Cortex XDR - Isolate Endpoint'),
                        [('playbook', 'Isolate Endpoint - Generic')],
                    )
                ],
            },
            'CVE_2021_44228': {
                'mandatory': True,
                'dependent_items': [
                    (
                        ('integration', 'Cortex XDR - XQL Query Engine'),
                        [('playbook', 'CVE-2021-44228 - Log4j RCE')],
                    )
                ],
            },
            'Traps': {
                'mandatory': True,
                'dependent_items': [
                    (
                        ('incident_field', 'incident_xdrresolvecomment'),
                        [('layout', 'Traps')],
                    )
                ],
            },
            'MajorBreachesInvestigationandResponse': {
                'mandatory': True,
                'dependent_items': [
                    (
                        ('incident_field', 'incident_lastmirroredintime'),
                        [('layout', 'Rapid Breach Response')],
                    ),
                    (
                        ('incident_field', 'incident_xdrmanualseverity'),
                        [('layout', 'Rapid Breach Response')],
                    ),
                    (
                        ('incident_field', 'incident_xdrmodificationtime'),
                        [('layout', 'Rapid Breach Response')],
                    ),
                ],
            },
        },
        'path': 'Packs/CortexXDR',
        'fullPath': '/Users/rshalem/dev/demisto/content/Packs/CortexXDR',
    },
    'DeprecatedContent': {
        'packsDependentOnThisPackMandatorily': {},
        'path': 'Packs/DeprecatedContent',
        'fullPath': '/Users/rshalem/dev/demisto/content/Packs/DeprecatedContent',
    },
    'Inventa': {
        'packsDependentOnThisPackMandatorily': {},
        'path': 'Packs/Inventa',
        'fullPath': '/Users/rshalem/dev/demisto/content/Packs/Inventa',
    },
    'CrowdStrikeFalconStreamingV2': {
        'packsDependentOnThisPackMandatorily': {},
        'path': 'Packs/CrowdStrikeFalconStreamingV2',
        'fullPath': '/Users/rshalem/dev/demisto/content/Packs/CrowdStrikeFalconStreamingV2',
    },
    'IntegrationsAndIncidentsHealthCheck': {
        'packsDependentOnThisPackMandatorily': {},
        'path': 'Packs/IntegrationsAndIncidentsHealthCheck',
        'fullPath': '/Users/rshalem/dev/demisto/content/Packs/IntegrationsAndIncidentsHealthCheck',
    },
    'TIM_SIEM': {
        'packsDependentOnThisPackMandatorily': {},
        'path': 'Packs/TIM_SIEM',
        'fullPath': '/Users/rshalem/dev/demisto/content/Packs/TIM_SIEM',
    },
    'ShiftManagement': {
        'packsDependentOnThisPackMandatorily': {},
        'path': 'Packs/ShiftManagement',
        'fullPath': '/Users/rshalem/dev/demisto/content/Packs/ShiftManagement',
    },
    'EmployeeOffboarding': {
        'packsDependentOnThisPackMandatorily': {},
        'path': 'Packs/EmployeeOffboarding',
        'fullPath': '/Users/rshalem/dev/demisto/content/Packs/EmployeeOffboarding',
    },
    'Campaign': {
        'packsDependentOnThisPackMandatorily': {
            'MajorBreachesInvestigationandResponse': {
                'mandatory': True,
                'dependent_items': [
                    (
                        (
                            'incident_field',
                            'incident_actionsoncampaignincidents',
                        ),
                        [('layout', 'Rapid Breach Response')],
                    ),
                    (
                        ('incident_field', 'incident_campaignclosenotes'),
                        [('layout', 'Rapid Breach Response')],
                    ),
                    (
                        ('incident_field', 'incident_campaignemailbody'),
                        [('layout', 'Rapid Breach Response')],
                    ),
                    (
                        ('incident_field', 'incident_campaignemailsubject'),
                        [('layout', 'Rapid Breach Response')],
                    ),
                    (
                        ('incident_field', 'incident_incidentsinfo'),
                        [('layout', 'Rapid Breach Response')],
                    ),
                    (
                        ('incident_field', 'incident_selectaction'),
                        [('layout', 'Rapid Breach Response')],
                    ),
                    (
                        ('incident_field', 'incident_selectcampaignincidents'),
                        [('layout', 'Rapid Breach Response')],
                    ),
                ],
            }
        },
        'path': 'Packs/Campaign',
        'fullPath': '/Users/rshalem/dev/demisto/content/Packs/Campaign',
    },
    'ThreatIntelReports': {
        'packsDependentOnThisPackMandatorily': {},
        'path': 'Packs/ThreatIntelReports',
        'fullPath': '/Users/rshalem/dev/demisto/content/Packs/ThreatIntelReports',
    },
    'CommonWidgets': {
        'packsDependentOnThisPackMandatorily': {
            'CommonDashboards': {
                'mandatory': True,
                'dependent_items': [
                    (
                        ('script', 'RSSWidget'),
                        [('dashboard', 'My Threat Landscape')],
                    ),
                    (
                        ('script', 'FeedIntegrationErrorWidget'),
                        [('dashboard', 'Threat Intelligence Feeds')],
                    ),
                ],
            }
        },
        'path': 'Packs/CommonWidgets',
        'fullPath': '/Users/rshalem/dev/demisto/content/Packs/CommonWidgets',
    },
    'EmailCommunication': {
        'packsDependentOnThisPackMandatorily': {},
        'path': 'Packs/EmailCommunication',
        'fullPath': '/Users/rshalem/dev/demisto/content/Packs/EmailCommunication',
    },
    'IAM-SCIM': {
        'packsDependentOnThisPackMandatorily': {},
        'path': 'Packs/IAM-SCIM',
        'fullPath': '/Users/rshalem/dev/demisto/content/Packs/IAM-SCIM',
    },
    'TIM_Processing': {
        'packsDependentOnThisPackMandatorily': {},
        'path': 'Packs/TIM_Processing',
        'fullPath': '/Users/rshalem/dev/demisto/content/Packs/TIM_Processing',
    },
}
