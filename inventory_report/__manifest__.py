{
    "name": "Inventory Report",
    "category": "Inventory",
    "author": "",
    "summary": "Inventory related report",
    "version": "1.0",
    "description": """
 custom report for Inventory  
        """,
    "depends": ['base','stock','product_attribute_inventory'],
    "data": [
        'data/data.xml',
        'wizzard/stock_transfer_report_wizzard.xml',
        'report/stock_transfer.xml',
        'wizzard/branchwise_stock_wizard.xml',
        'wizzard/serial_wise_warranty_check.xml',
        'wizzard/current_stock_with_serial.xml',
        'report/current_stock_serial_report.xml'
    ],
    "installable": True,
}
