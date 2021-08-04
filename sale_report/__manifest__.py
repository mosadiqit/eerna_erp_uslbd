# -*- coding: utf-8 -*-

{
    "name": "Sales Report",
    "category": "Sales",
    "author": "",
    "summary": "Sales summary report",
    "version": "1.0",
    "description": """
 custom report for daily sale summary 
        """,
    "depends": ["sale_management", "gts_branch_management",'product_attribute_inventory','usl_customer_area'],
    "data": [
        'data/data.xml',
        'wizard/sale_order_summary_wizard.xml',
        'report/sale_summary.xml',
        'wizard/Daily_Sales_Details_wizard.xml',
        'report/daily_sales_details.xml',
        'wizard/sale_report_detail_wizard.xml',
        'report/invoice_datewise_sale_summary_report.xml',
        'wizard/invoice_datewise_sales_summary.xml',
        'report/sale_detail.xml',
        'wizard/group_brand_item_wise_summery.xml',
        'report/group_brand_item_report.xml',
        'wizard/sales_summary_report_with_serial_no.xml',
        'report/sale_summary_report_serial.xml',
        'wizard/sale_summary_location_wise.xml',
        'report/sale_summary_location_wise_report.xml',
        'wizard/sale_report_buyer_wise.xml',
        'report/sale_buyerwise_report.xml',
        'wizard/sales_summery_report_area_wise.xml',
        'wizard/aged_customer_list.xml',
        'report/aged_customer_list_report.xml',
        'report/area_wise_sales_summery_report.xml',
        'report/smart_invoice_report_format.xml'

    ],
    "installable": True,
}
