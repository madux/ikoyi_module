#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Maduka Sopulu Chris kingston
#
# Created:     20/04/2018
# Copyright:   (c) kingston 2018
# Licence:     <your licence>
#--------------------------------------------------------------------
{
    'name': 'Ikoyi Club ERP',
    'version': '10.0.1.0.0',
    'author': 'Maduka Sopulu/ Vascon Solutions',
    'description': """ERP Application for managing
                     the whole activities of ikoyi club""",
    'category': 'Procurement',

    'depends': ['base', 'mail', 'purchase', 'branch', 'web_digital_sign', 'stock', 'hr'],
    'data': [
        'security/security_group.xml',
        'security/menu_views_security.xml',
        'sequence/sequence.xml',
        'views/ikoyi_procurement_views.xml',
        'views/hr_inherit.xml',
        'views/requisition_view.xml',
        'views/goods_return_views.xml',
        'views/product_views.xml',
        'views/report_mandate_template.xml',
        'views/hr_capital_development.xml',
        'views/hr_power.xml',
        'views/hr_offer_management.xml',
        'views/hr_corps_view.xml',
        'views/hr_permanent_recruit.xml',
        'views/all_report_id.xml',
        'views/costing_reporting_wizard.xml',
        'views/costing_management.xml',
        'reports/grn_note.xml',
        'reports/siv_note.xml',
        'reports/credit_debit_note.xml',
        'reports/single_mandate.xml',
        'reports/reports_inherits.xml',
        'reports/purchase_print.xml',
        'views/report_grn_two.xml',
        'views/report_grn.xml',
        # 'views/hr_leave.xml',
        # 'reports/mandate_report_view.xml',
        'wizard/mandate_report_view.xml',
        'wizard/view_grn_wizard_view.xml',
        'security/ir.model.access.csv',
    ],
    'price': 4200.99,
    'currency': 'USD',
    'sequence': 1,


    'installable': True,
    'auto_install': False,
}
