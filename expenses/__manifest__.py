# -*- coding: utf-8 -*-
{
    'name': "expenses",

    'summary': """
        Modifica la forma en la que se registran contablemente los gastos""",

    'author': "SIE Center",
    'website': "http://www.siecenter.com.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Expenses',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr_expense','account_accountant'],

    # always loaded
    'data': [
        'security/groups.xml',
        'views/views.xml',
        #'views/res_partner.xml',
    ],
}
