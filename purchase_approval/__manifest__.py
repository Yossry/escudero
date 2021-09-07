# -*- coding: utf-8 -*-
{
    'name': "Purhase Approval",
    

    'description': """
        Módulo para la aprobación de las compras realizadas
    """,

    'author': "SIE Center",

    'website': "http://www.qualsys.com.mx",

    'version': '0.1',

    
    'depends': [
    	'base',
    	'purchase'
	],

    
    'data': [          
        'security/groups.xml',      
        'views/views.xml',        
    ],
    
}