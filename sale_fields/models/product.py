# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

ACCOUNT_DOMAIN = "['&', '&', '&', ('deprecated', '=', False), ('internal_type','=','other'), ('company_id', '=', current_company_id), ('is_off_balance', '=', False)]"

class ProductTemplate(models.Model):
    _inherit = 'product.template'


    property_account_income_id_par_rel = fields.Many2one('account.account', 
    	company_dependent=True, 
    	string="Cuenta de ingreso Partes Relacionadas",
        domain=ACCOUNT_DOMAIN,
        help="Indique la cuenta contable del producto para clientes Partes Relacionadas.")