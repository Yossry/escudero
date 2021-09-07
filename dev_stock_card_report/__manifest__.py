# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################

{
    'name': 'Product Stock Card Report',
    'version': '14.0.1.0',
    'category': 'Warehouse',
    'sequence':1,
    'summary': 'Print Stock Card Report in PDF/EXCEl | product stock report | stock rotation report | real-time stock in and stock out report | stock ledger report | stock incoming ledger | stock outgoing ledger | Inventory report | Inventory Valuation',
    'description': """
        Odoo application will help to print Stock Card PDF and generate Excel Report.

Product Stock Card Report
Odoo Product Stock Card Report
Manage product stock card report 
Odoo manage product stock card report 
Print Stock Card PDF Report
Odoo Print Stock Card PDF Report
Manage Print Stock Card PDF Report
Odoo manage Print Stock Card PDF Report
Generate Stock Card Excel Report
Odoo Generate Stock Card Excel Report
Manage Generate Stock Card Excel Report
Odoo manage Generate Stock Card Excel Report
Filter Product By Date, Product and Product Category
Odoo Filter Product By Date, Product and Product Category
Manage Filter Product By Date, Product and Product Category
Odoo manage Filter Product By Date, Product and Product Category
Print stock card report 
Odoo print stock card report 
Manage stock card report 
Odoo manage stock card report 
Stock card PDF report 
Odoo stock card PDF report 
Manage Stock card PDF report 
Odoo manage Stock card PDF report 
Product stock card 
Odoo Product Stock Card 
Manage Product Stock card 
Odoo Manage Product Stock Card 
Stock card report 
Odoo Stock card Report 
Manage Stock card report 
Odoo Manage Stock Card Report 
Print Stock Card PDF Report
Odoo Print Stock Card PDF Report
 Generate Stock Card Excel Report
Odoo  Generate Stock Card Excel Report
Filter Product By Date, Product and Product Category
Odoo Filter Product By Date, Product and Product Category
Manage Stock Card PDF 
Odoo Manage print stock card PDF 
Manage Odoo Print Stock Card PDF 
Stock Card Excel Report 
Odoo Stock card Excel Report 


            """,
    'author': 'DevIntelle  Consulting Service Pvt. Ltd',
    'website': 'http://devintellecs.com/',
    'depends': ['sale_management','sale_stock', 'stock_account'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/dev_stock_card_view.xml',
        'report/header.xml',
        'report/stock_card_report.xml',
        'report/report_menu.xml',
        #'models/stock_quants.xml',
        ],
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    
    # author and support Details =============#
    'author': 'DevIntelle Consulting Service Pvt.Ltd',
    'website': 'http://www.devintellecs.com',    
    'maintainer': 'DevIntelle Consulting Service Pvt.Ltd', 
    'support': 'devintelle@gmail.com',
    'price':25.0,
    'currency':'EUR',
    #'live_test_url':'https://youtu.be/A5kEBboAh_k',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
