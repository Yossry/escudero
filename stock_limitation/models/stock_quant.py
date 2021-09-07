# -*- coding: utf-8 -*-

from odoo import api, models


class stock_quant(models.Model):
    """
    Override to avoide security bugs
    """
    _inherit = 'stock.quant'

    @api.model
    def _get_removal_strategy(self, product_id, location_id):
        """
        Re-write to get removal strategy for parent under sudo
        """
        if product_id.categ_id.removal_strategy_id:
            return product_id.categ_id.removal_strategy_id.method
        loc = location_id
        while loc:
            if loc.removal_strategy_id:
                return loc.removal_strategy_id.method
            loc = loc.sudo().location_id
        return 'fifo'
