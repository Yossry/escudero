# -*-coding: utf-8 -*-
{
    'name': "Stock card (PDF & Excel)",

    'summary': "Add an report stock card in inventory",

    'description': """
        Print stock card.

        Print a stock card for a location wether it is for a internal,
        view, inventory, production or scrapped location. This module
        will give you the in, out and the balance of location between
        a period.
    """,

    'author': "HyD Freelance",
    'website': "http://",
    'category': u'Warehouse',
    'version': '1.0.1',
    'license': 'AGPL-3',
    'depends': ['stock', 'web', 'report_xlsx'],

    'data': [

        # reports
        'reports/paper.xml',
        'reports/stock_card_report.xml',
        'reports/stock_card_details_report.xml',

        # views
        'views/action_manager.xml',

        # wizards
        'wizards/stock_card_wizard_views.xml'
    ],
    'demo': [],
    'installable': True,
    'price': 80,
    'currency': 'EUR',
    'images': ['static/images/main_screenshot.png'],
    "live_test_url": "https://youtu.be/ZOwO8lxYhBA",
}
