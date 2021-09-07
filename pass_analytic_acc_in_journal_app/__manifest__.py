# -*- coding: utf-8 -*-

{
    'name': 'Payment Voucher with Analytic Account & Analytic Tag',
    "author": "Edge Technologies",
    'version': '14.0.1.0',
    'live_test_url': "https://youtu.be/UxgQs96sam0",
    "images":['static/description/main_screenshot.png'],
    'summary': "Payment Voucher Analytic Account payment receipt with Analytic Account Account Voucher with Analytic Tag Analytic Account on payment internal transfer analytic account Analytic payment voucher Analytic Tag Payment Voucher with Cost Centre Analytic costing",
    'description': """This App helps to Allows to configure Analytic Account and Tags in Payment then Pass Automatically in Journal Entries. User can configure analytic account & tag for both manual and invoice payment.
    
Payment Voucher with Analytic Account & Analytic Tag
payment receipt with Analytic Account & Analytic Tag
Analytic Account
payment receipt Analytic Tag
payment receipt Analytic Account
Analytic Account payment receipt
Analytic Tag
internal transfer payment
internal transfer analytic account
analytic account internal transfer payment
Analytic payment voucher payment receipt Analytic account
voucher with Analytic account 
voucher Analytic Tag
Payment Voucher with Cost Centre Analytics
Analytic account Payment
Create Payment With Analytic account and Tags
Add Analytic accounting
voucher Analytic account
payment voucher Analytic Tag
payment vouhcer analytical account


    """,
    "license" : "OPL-1",
    'depends': ['base','payment','account'],
    'data': [
            'security/analytic_account_group.xml',
            'views/account_payment_form_inherit.xml',
            ],
    'installable': True,
    'auto_install': False,
    'price': 35,
    'currency': "EUR",
    'category': 'Accounting',
}
