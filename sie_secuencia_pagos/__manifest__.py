# -*- coding: utf-8 -*-
{
    'name': "Secuencia Pagos",
    'summary': """Separación de secuencias de pagos de cliente y a provedores""",
    'author': "SIE Center",
    'category': 'Accounting',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account','sale','purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_journal.xml',
        #'views/templates.xml',
    ],
}
