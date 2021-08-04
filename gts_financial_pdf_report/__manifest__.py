# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'GTS Financial PDF Reports',
    'version' : '13.0.0.1',
    'summary': 'GTS Financial PDF Reports in community odoo v13',
    'sequence': 1,
    'description': """
        ALL Financial PDF Reports or Finance report  or Financial Reports - Balance Sheet, Profit and Loss, General Ledger,
        Trial Balance, Aged Partner balance, Partner Ledger, Sale/Purchase Journal 
        in odoo version 13.
    """,
    'category': 'Accounting',
    'website': 'https://www.geotechnosoft.com',
    'author': 'Geo Technosoft',
    'depends': ['base', 'account', 'sale', 'account_check_printing'],
    'data': [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'data/account_pdc_data.xml',
        'data/cash_flow_data.xml',
        'views/accounting_menu.xml',
        'views/account_financial_report_view.xml',
        'views/account_report.xml',
        'views/account_financial_report_data.xml',
        'views/report_trialbalance.xml',
        'views/report_generalledger.xml',
        'views/report_partnerledger.xml',
        'views/report_financial.xml',
        'views/report_agedpartnerbalance.xml',
        'views/account_menuitem.xml',
        'report/account_bank_book_view.xml',
        'report/account_cash_book_view.xml',
        'report/account_day_book_view.xml',
        'wizard/account_bank_book_wizard_view.xml',
        'wizard/account_cash_book_wizard_view.xml',
        'wizard/account_day_book_wizard_view.xml',
        'wizard/account_report_print_journal_view.xml',
        'wizard/account_report_partner_ledger_view.xml',
        'wizard/account_report_general_ledger_view.xml',
        'wizard/account_report_trial_balance_view.xml',
        'wizard/account_financial_report_view.xml',
        'wizard/account_report_aged_partner_balance_view.xml',
    ],
    'qweb': [],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 15.00,
    'currency': 'EUR',
    'license': 'OPL-1',
}