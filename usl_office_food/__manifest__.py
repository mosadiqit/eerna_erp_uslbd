# -*- coding: utf-8 -*-
{
    'name': "usl_office_food",

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
    'depends': ['base', 'hr', 'mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/food_reserve_seq.xml',
        'data/date_reserve_corn.xml',
        'views/web_asset_backend_template.xml',

        # 'views/templates.xml',

        'views/employee_meal_reserve.xml',
        'views/holiday_month_date.xml',
        'views/inherit_hr_attendence_view.xml',
        'views/views.xml',
        'views/current_month_report_server_action.xml',
        'report/this_month_reserve_and_eat_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'qweb': [
        "static/src/xml/attendance.xml",
    ],
}
