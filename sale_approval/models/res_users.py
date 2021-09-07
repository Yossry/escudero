# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, SUPERUSER_ID, _

class Users(models.Model):
    _inherit = "res.users"
    
    sale_order_can_approve = fields.Selection([('yes', 'Yes'), ('no', 'No')], 'Aprobador Ventas',default='no')
    sale_order_amount_limit = fields.Float("(SO) Amount Limit", digits=(16, 0))
    sale_order_discount_limit = fields.Float("(SO) Discount Limit", digits=(16, 0))
    amount_purchase_approval_min = fields.Float('Monto minimo Compras')
    amount_purchase_approval_max = fields.Float('Monto máximo Compras')
    purchase_order_can_approve = fields.Boolean('Aprobador de Compras')



   