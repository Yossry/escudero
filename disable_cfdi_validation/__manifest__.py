# -*- coding: utf-8 -*-
{
    'name': "Disable CFDI Validation",

    'summary': """
        Agrega una opción para saltar la validacion de xml por el modulo validate_cfdi""",

    'author': "SIE Center / Samuel Santana",
    'website': "http://www.siecenter.com.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Invoicing',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['validate_cfdi'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_partner.xml',
    ],
}
