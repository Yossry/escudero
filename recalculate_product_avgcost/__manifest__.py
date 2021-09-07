# -*- coding: utf-8 -*-
##############################################################################
#
#    SIE CENTER custom module for Odoo
#    Copyright (C) 2021
#    @author: @cyntiafelix
#
##############################################################################

{
    'name': "Recalculate Average Cost",
    'summary': """SIE CENTER custom module for Recalculate Inventory Valuation and Average Cost""",
    'version': '14.0.1.0.1',
    'category': 'Accounting',
    'author': "SIE CENTER",
    'license': 'Other proprietary',
    'application': False,
    'installable': True,
    'depends': [
        'base',
        'account',
        'product',
        'stock',
        'stock_force_date_app'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
    ]
}
