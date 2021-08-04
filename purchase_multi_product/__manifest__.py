{
    # App information

    'name': "Purchase Multiple Products",
    'category': 'Purchase',
    'version': '13.0',
    'summary' : 'Save your time by easily manage large Purchase Orders through Importing/Mass updating bulk Purchase lines in one time',
    'license': 'OPL-1',

    # Author
    'author': 'Er. Vaidehi Vasani',
    'maintainer': 'Er. Vaidehi Vasani',

    # Dependencies

    'depends': ['purchase'],
    'data': [
        'wizard/select_multi_products.xml',
        'views/purchase_order_ext_ept.xml'
    ],

    # Technical
    'images': ['static/description/purchase_multi_product_coverpage.jpg'],
    # Technical
    'installable': True,
    'auto_install': False,
    'application': True,
    'price': 00.00,
    'currency': 'USD',

}
