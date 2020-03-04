# -*- coding: utf-8 -*-
{
    'name' : 'Custom Sales Report',
    'version' : '1.0',
    'summary': 'Custom report for the company sales',
    'sequence': 16,
    'category': 'Sales',
    'description': """
Custom Sales Report
=====================================
Sales report that will generate a pdf report for a sales person for specific time duration.
    """,
    'category': 'Accounting',
    'website': 'http://www.surekhatech.com/blog',
    'images' : [],
    'depends' : ['base_setup', 'report', 'sale'],
    'data': [
        'wizard/salesperson_report_view.xml',
        'views/sales_report_report.xml',
        'views/report_salesperson.xml'
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
