# -*- coding: utf-8 -*-
{
    'name': "accounting_report",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.uslbd.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account','gts_branch_management','usl_accounting_module', 'report_xlsx'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'wizard/collection_statement_wizard.xml',
        'report/collection_statement.xml',
        'wizard/payment_statement_wizard.xml',
        'report/payment_statement.xml',
        'wizard/sales_gross_profit_wizard.xml',
        'report/sales_gross_statement.xml',
        'wizard/aged_balance_details_wizard.xml',
        'report/report_agedpartnerbalance_details.xml',
        'wizard/sales_gross_profit_details_wizard.xml',
        'report/sales_gross_details_statement.xml',
        'wizard/cheque_report_branch_wise.xml',
        'report/branchwise_report.xml',
        'wizard/Dishonor_Report_wizard.xml',
        'report/dishonored_cheque.xml',
        'wizard/Honor_Report_Wizard.xml',
        'report/honor_cheque.xml',

        'wizard/cheque_in_hand_report.xml',
        'report/in_hand_report.xml',

        'wizard/collected_cheque_without_treatment.xml',
        'report/collected_cheque_without_treatment_report.xml',

        'wizard/collection_against_dishonor_cheque_wizard.xml',
        'report/collection_against_dishonor_cheque_report.xml',

        'wizard/cheque_history_report.xml',
        'report/cheque_history.xml',
        'report/money_recept.xml',
        'wizard/all_cheque_report.xml',
        'wizard/credit_list_report.xml',
        'report/credit_list_report.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
