# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class StockWarehouse(models.Model):
    _inherit = "stock.warehouse"

    analytic_account_id = fields.Many2one('account.analytic.account', 'Cuenta Analitica', help="Cuenta analitica del almacen")
    analytic_account_ids = fields.Many2many('account.analytic.account', 'id', help="Cuenta analitica del almacen")
    journal_id = fields.Many2one('account.journal', string='Diario de Facturas de Cliente')
    journal_id_supplier = fields.Many2one('account.journal', string='Diario de Facturas de Proveedor')