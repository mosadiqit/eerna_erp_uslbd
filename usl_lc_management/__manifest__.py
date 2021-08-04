# -*- coding: utf-8 -*-
{
    'name': "usl_lc_management",

    'summary': """
        USL lc management app""",

    'description': """
        This module is for lc management.
        Developed by: USL systems ltd.
    """,

    'author': "USL systems Ltd.",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','usl_univat_setup','bank_info'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/lc_management_form.xml',
        'data/sequence.xml',
        'report/usl_lc_report.xml',
        'report/usl_report.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
