# -*- coding: utf-8 -*-
{
    'name': "custom_sale_invoice_report",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "S. M. EMRUL BAHAR",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/data.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/stock_picking_inherit.xml',
        'report/custom_invoice_report.xml',
        'report/sale_invoice_report_inherit.xml',
        'report/invoice_challan_report_template.xml',
        'report/deliverySlip_with_signature.xml',
        'report/transfer_mushak_6_5.xml',
        'report/nbr_report.xml',
        'report/nbr_report_view.xml',
        'wizard/customer_Bp_wizard.xml',
        'report/Customer_Bp_report.xml',
        'report/stock_report_deliveryslip_inherit.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
