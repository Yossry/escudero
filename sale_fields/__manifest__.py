# -*- coding: utf-8 -*-
{
    'name': "Campos Ventas",

    'summary': """
        Añade campos al modelo sale_order""",

    'description': """
        
    """,

    'author': "SIE Center",
    'website': "http://www.siecenter.com.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale_management', 'crm'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order.xml',
        'views/partner.xml',
        'views/product.xml',
        'views/template_quotation.xml',
        'views/sale_template.xml',
        'views/template_quotation_sdm.xml',
    ],
}
