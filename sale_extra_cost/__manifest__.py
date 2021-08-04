# -*- coding: utf-8 -*-
{
    'name': "sale_extra_cost",

    'summary': """
        This module for Business promotion cost maintain.""",

    'description': """
        This module will be work as invoice extra cost functionality like, Business promotion cost.
        User will input the BP amount at sale order then it will be proceed to sales invoices. Accounting
        integration will be done automatically.
    """,
    "version": "13.0.1.2.0",
    'author': "Mostofa Zaman",
    'website': "http://www.uslbd.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['sale','account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'security/field_visible.xml',
        'views/sales_other_cost_acc_map.xml'
    ],
    "installable": True,
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
