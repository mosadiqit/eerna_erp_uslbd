# -*- coding: utf-8 -*-
{
    'name': "usl_restriction_setup",

    'summary': """Company wise user & back order creation restriction in community odoo v13""",

    'description': """
        Company wise user & back order creation restriction in community odoo v13
    """,

    'author': "Unisoft Systems Limited",
    'website': "http://www.uslbd.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Security',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','contacts','sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/company_wise_user_create_restriction.xml',
        'views/company_wise_back_order_restriction.xml',
        'views/sale_order_unlock_button_hide.xml',
        'views/menuitem.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'images': ['static/description/icon.png'],
}
