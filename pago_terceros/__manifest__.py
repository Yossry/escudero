# -*- coding: utf-8 -*-
{
    'name': "Pago por aplicación de terceros",

    'summary': """
        Añade la opción de incluir pago por aplicación de terceros en facturas de proveedor""",

    'author': "SIE Center",
    'website': "http://www.siecenter.com.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account_accountant'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'wizards/pago_tercero.xml',
        'views/account_move.xml',
    ]
}
