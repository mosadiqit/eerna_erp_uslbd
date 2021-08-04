# -*- coding: utf-8 -*-
{
    'name': "Cheque Management",

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
    'depends': ['base','account', 'gts_branch_management', 'bank_info', 'custom_customer_payment_approval', 'account_payment_approval'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/cheque_model.xml',
        'views/batch_payment.xml',
        'views/cheque_treatment.xml',
        'views/account_payment_inherit.xml',
        'views/res_partner_view.xml',
        'views/menu_item.xml',
        'wizard/account_report_aged_partner_balance_view.xml',
        # 'report/money_recept.xml',
        'report/report_agedchequeinhandbalance.xml',
        'report/report_menu.xml',
        'data/data.xml',
        'data/corn.xml',
        'security/security.xml'
        # 'views/views.xml',
        # 'views/templates.xml',
        # 'views/account_payment_inherit.xml'
        # manifest of check management
        # check
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],

}

