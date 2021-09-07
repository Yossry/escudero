# -*- coding: utf-8 -*-
##############################################################################
#
#    SIE CENTER custom module for Odoo
#    Copyright (C) 2021
#    @author: @cyntiafelix
#
##############################################################################

from odoo import api, fields, models
from odoo.exceptions import Warning, ValidationError
from collections import defaultdict
from odoo.tools import float_is_zero
import dateutil.parser

class SIECenter_StockMove(models.Model):
    _inherit = "stock.move"

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost):
        self.ensure_one()
        force_date = self.picking_id.force_date
        AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

        move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
        if move_lines:
            if force_date:
                date = dateutil.parser.parse(str(force_date)).date()
            else:
                #date = self._context.get('force_period_date', fields.Date.context_today(self))
                date = self._context.get('force_period_date', self.date)

            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': description,
                'stock_move_id': self.id,
                'stock_valuation_layer_ids': [(6, None, [svl_id])],
                'move_type': 'entry',
            })
            new_account_move._post()
