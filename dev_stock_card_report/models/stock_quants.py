# -*- coding: utf-8 -*-

import time
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockQuant(models.Model):
	_inherit = 'stock.quant'

	standard_price = fields.Float(string='Costo Unitario',related='product_id.standard_price')
	category_id = fields.Many2one(string='Categoría de producto',related='product_id.categ_id',store=True)
