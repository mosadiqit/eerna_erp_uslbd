
{
    'name': 'Custom Permission',
    'version': '13.0.1.0.1',
    'category': 'Warehouse',
    'summary': 'Custom Permission',
    'author': 'Unisoft System Ltd.',
    'company': 'Unisoft System Ltd.',
    'maintainer': 'Unisoft System Ltd.',
    'images': ['static/description/banner.png'],
    'website': 'http://www.uslbd.com/',
    'depends': [
        'sale_management',
    ],
    'data': [
        'security/sales_reset_to_draft_security.xml',
        'views/sales_reset.xml',
        # 'views/delivery_on_invoice_posted.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,

}
