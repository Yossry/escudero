# -*- coding: utf-8 -*-
{
    'name': "validate_cfdi",

    'summary': """
        Valida que el XML adjunto a facturas de proveedor corresponda a lo capturado""",

    'description': """
        Establece la referencia de la factura, la fecha y el Folio Fiscal a facturas de Proveedor
    """,

    'author': "SIE Center / Angeles Gervacio",
    'website': "http://www.siecenter.com.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Invoicing',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account_accountant'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/purchase.xml',
        'security/groups.xml',

    ],
}
