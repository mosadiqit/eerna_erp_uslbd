# -*- coding: utf-8 -*-
{
    'name': "usl_recived_forigin_purchased",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock' ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        # 'views/stock_move_operation_new.xml',
        'views/stockpickingvliewinharit.xml',
        # 'views/view_foreign_purchase_order_form_inharit.xml',
        # 'views/createStockingPickingViewForFPO.xml',
        # 'views/inherit_stock_picking.xml',
        'views/delivery_button_hide.xml'

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
