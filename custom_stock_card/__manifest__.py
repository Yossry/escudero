# -*-coding: utf-8 -*-
{
    'name': "Stock card custom",

    'summary': "Add custom functionalities to hyd_stock_card (by HyD Freelance)",

    'author': "SIE Center / Samuel Santana",
    'website': "http://www.siecenter.com.mx",
    'version': '0.1',
    'depends': ['hyd_stock_card', 'stock_force_date_app', 'report_xlsx'],

    'data': [

        # reports
        # 'reports/paper.xml',
        'reports/stock_card_report.xml',
        'reports/stock_card_details_report.xml',

        # # views
        # 'views/action_manager.xml',

        # # wizards
        'wizards/stock_card_wizard_views.xml'
    ],
    'demo': [],
}
