# -*- coding: utf-8 -*-

from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    forma_pago = fields.Selection(
        selection=[
            ('credito', 'Crédito'),
            ('contado', 'Contado'),
        ]
    )
    tiempo_entrega_selection = fields.Selection(
        selection=[
            ('inmediata', 'Inmediata'),
            ('programa', 'Entrega según programa de suministro'),
        ]
    )
