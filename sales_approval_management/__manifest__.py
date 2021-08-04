# -*- coding: utf-8 -*-
{
    'name': "sales_approval_management",

    'summary': """
        Sales Approval Management System. Everything you need to know for sales approval.
        Sales Order Approval, Customer Bill Approval, Customer Credit Note Approval.
        """,

    'description': """
        This module will help you to manage sales approval system. You can configure sales
        approvar for specific approval system.
    """,

    'author': "Unisoft System Limited",
    'website': "http://www.uslbd.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'web_notify'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'security/security.xml',
        # 'wizard/sale_order_cancel.xml',
        # 'views/sale_views_inherit.xml',
        'views/sale_approval_settings.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
