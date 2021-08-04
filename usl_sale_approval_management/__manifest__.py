# -*- coding: utf-8 -*-
{
    'name': "usl_sale_approval_management",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Md. Ruhullahil kabir on behalf of unisoft ",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'web_notify'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',

        # 'views/views.xml',
        # 'views/templates.xml',
        # 'views/saleApprovalInharit.xml',
        'wizard/sale_order_cancel.xml',
        'views/sale_views_inherit.xml',
        'views/sale_aprove_mng.xml',
        'views/account_move_inherit.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
