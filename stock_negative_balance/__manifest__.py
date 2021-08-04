# -*- coding: utf-8 -*-
{
    'name': "Stop Negative Stock Quantity",
    'summary': """ Disallow negative stock """,
    'description': """ 

Stock Negative Quantity
========================

Disallow negative quantity when creating sale, purchse and inventory. 
---------------------------------------------------------------------""",

    'author': "Wangoes Technology",
    'website': "http://www.wangoes.com",
    'category': 'Sale Purchse Inventory',
    'version': '12.0.1.0',
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',

    'depends': ['base','sale','stock','purchase','sale_management',],
    'installable': True,
    'data': [
        'views/purchase_neg_stock.xml',
    ],
}
