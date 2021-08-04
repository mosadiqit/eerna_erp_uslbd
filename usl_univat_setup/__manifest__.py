# -*- coding: utf-8 -*-
{
    'name': "usl_univat_setup",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "UniSoft System Ltd",
    'website': "http://www.uslbd.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['mail', 'base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/setup/product_hs_code.xml',
        'views/setup/other_tax_info.xml',
        'views/setup/pc_value_added_item.xml',
        'views/setup/vat_deduction_services.xml',
        'views/basic/base_menu.xml',
        'views/setup/add_hs_code_in_product_template.xml',
        'views/basic/required_GSTIN_for_company.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
