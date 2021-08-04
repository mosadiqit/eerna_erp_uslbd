# -*- coding: utf-8 -*-
{
    'name': "usl_menu_hide",

    'summary': """
        This module will be implemented group wise menu show and hide permission.""",

    'description': """
        USL menu permission app.
    """,

    'author': "Unisoft Systems Limited (BD)",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','website','website_sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/menu_data.xml',
        'views/menu_hide_views.xml',
        'views/override_menu.xml',
        'views/views.xml',
        'views/templates.xml',
        'security/security.xml',
        # 'views/menu_data.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    # 'qweb': ['static/src/xml/many2many_checkboxes.xml', ]
}
