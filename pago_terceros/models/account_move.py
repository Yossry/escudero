# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import Warning


class AccountMove(models.Model):
    _inherit = 'account.move'

    apply_pago_tercero = fields.Boolean(string="Pago de Tercero Aplicado", default=False, readonly=True) 
    proveedor_pago_tercero = fields.Many2one(string="Proveedor de Tarjeta de Crédito", comodel_name="res.partner", readonly=True)
        #domain=[('type','=','product')])


    