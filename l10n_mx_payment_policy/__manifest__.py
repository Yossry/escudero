# -*- coding: utf-8 -*-
{
    'name': "Politica de Pago PPD/PUE",

    'summary': """
        Desactiva el cálculo automatico de la politica de pago en base a la fecha de vencimiento.""",

    'description': """
        Desactiva el cálculo automatico de la politica de pago en base a la fecha de vencimiento.
    """,

    'author': "SIE Center / Angeles Gervacio",
    'website': "http://www.siecenter.com.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account_accountant'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_move.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
