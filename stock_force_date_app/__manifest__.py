# -*- coding: utf-8 -*-
{
    'name': 'Force date in Stock Transfer and Inventory Adjustment',
    "author": "Edge Technologies",
    'version': '14.0.1.0',
    'live_test_url':"https://youtu.be/dPuODkkjbDA",
    "images":['static/description/main_screenshot.png'],
    'summary': "Stock Force Date Inventory force date Inventory Adjustment force date Stock Transfer force date stock picking force date receipt force date shipment force date delivery force date in stock backdate stock back date inventory back date receipt back date",
    'description': """ 
    	This Odoo module will helps you to allow stock force date in picking operations and inventory adjustment. auto pass stock force date in stock move when validate picking operations and inventory adjustment.
    """,
    "license" : "OPL-1",
    'depends': ['base','stock','purchase','purchase_stock','stock_account'],
    'data': [
        'security/stock_force_security.xml',
        'views/stock_inventory.xml',
        ],
    'installable': True,
    'auto_install': False,
    'price': 20,
    'currency': "EUR",
    'category': 'Warehouse',
}
