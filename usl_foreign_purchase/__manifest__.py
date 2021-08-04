# Copyright (C) 2019 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Foreign Purchase Orders",
    "category": "Purchase",
    "license": "AGPL-3",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "version": "13.0.1.0.0",
    "website": "https://github.com/OCA/purchase-workflow",
    "summary": "Foreign Purchase Orders",
    "depends": ["purchase", "web_action_conditionable","product",'stock','stock_landed_costs','usl_univat_setup','usl_product_module'],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/sequence.xml",
        "data/ir_cron.xml",
        "data/data.xml",
        "wizard/create_foreign_purchase_orders.xml",
        # "views/purchase_config_settings.xml",
        "views/foreign_purchase_order_views.xml",
        'views/stock_landed_cost_inherit_views.xml',
        # "views/purchase_order_views.xml",
        "report/templates.xml",
        "report/report.xml",
        "report/foreign_purchase_order_costing_report.xml",
        "views/template.xml",
        "views/account_move_inherit.xml",
        "views/InheritStockLandedCostLines.xml",
        "views/lc_management_form.xml",
        "views/foreign_p_o_state.xml",
        "views/foreign_p_order_kanban.xml",
        "views/forign_p_o_product_kanban.xml",

        # "views/product_template_inheritance.xml"
        "wizard/foreign_purchase_order_costing_report_wizzard.xml",

    ],
    "installable": True,
    'images': ['static/description/icon.png'],
}
