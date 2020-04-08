# -*- coding: utf-8 -*-
{
    'name' : 'Hotel Report',
    'version' : '1.0',
    'summary': 'Custom report for the hotel sales',
    'sequence': 16,
    'category': 'hotel',
    'author': 'Maduka Sopulu',
    'description': """
Custom Sales Report
=====================================
Sales report that will generate a pdf report for a sales person for specific time duration.
    """,
    'category': 'Accounting',
    'images' : [],
    'depends' : ['base_setup', 'hotel','report', 'sale'],
    'data': [
        'wizard/hotels_report_view.xml',
        'views/report_hotels_report.xml',
        'views/hotels_report_report.xml'
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
