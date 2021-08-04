# -*- coding: utf-8 -*-
# © 2020 Unisoft Systems Limited (http://www.uslbd.com)
# @author Mostofa Zaman <mostofa.zaman@uslbd.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Default Warehouse on Sale Order",

    'summary': """
        Base on user default warehouse sales order user wise warehouse will be set automatically""",

    'description': """
Default Warehouse on Sale Order
-------------------------------
        By this module you will get default warehouse suggestion for delivery the product. For get the
        default warehouse selection automatically you have to set the user default warehouse on user preferences 
        settings.
        If you set the user default warehouse at user settings then at the sales quotation and sales order form you will 
        find the same warehouse otherwise system take the company default warehouse.
        
        This module develop by Mostofa Zaman from Unisoft Systems Limited.
        <mostofa.zaman@uslbd.com>
    """,

    'author': "Unisoft Systems Limited",
    'website': "http://www.uslbd.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sale Management',
    'version': '13.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['sale','purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}