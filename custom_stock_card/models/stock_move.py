# -*- coding: utf-8 -*-
from odoo import fields, models


class StockMove(models.Model):
	_inherit = 'stock.move'

	product_reference = fields.Char(string='Referencia de producto',related='product_id.default_code', store=True)
	picking_force_date = fields.Datetime(string='Fecha forzada',related='picking_id.force_date', store=True)