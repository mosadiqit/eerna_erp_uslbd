# -*- coding: utf-8 -*-
{
    'name': "inventory_approval_management",

    'summary': """
        Inventory Approval Management System. Everything you need to know for Inventory approval.
        Inventory Transfer Approval.
        """,

    'description': """
        This module will help you to manage Inventory approval system. You can configure Inventory
        approval for specific approval system.
    """,

    'author': "Unisoft System Limited",
    'website': "http://www.uslbd.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'inventory',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'web_notify'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'security/security.xml',
        'views/inventory_approval_settings.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
