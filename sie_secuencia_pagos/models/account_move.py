# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.tools.misc import format_date
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _get_last_sequence_domain(self, relaxed=False):
        where_string, param = super(AccountMove, self)._get_last_sequence_domain(relaxed)
        _logger.warning("---------------------------------------")
        _logger.warning(self.sequence_prefix)
        #payment = self.env["account.payment"].search("move_id", "=", self.id)
        where_string += " AND sequence_prefix != %(prefix)s"
        param['prefix'] = "%s/%04d/%02d/" % (self.journal_id.code_exit, self.date.year, self.date.month)
        return where_string, param
    
    @api.model_create_multi
    def create(self, vals_list):
        moves = super(AccountMove, self).create(vals_list)
        for move in moves:
            statement_line = self.env["account.bank.statement.line"].search([("move_id", "=", move.id)], limit=1)            
            if statement_line and statement_line.amount < 0 and move.journal_id.type == 'bank' and move.journal_id.code_exit:
                move._set_custom_move_sequence()
                #pay.sequence_prefix = "%s/%04d/%02d/" % (pay.journal_id.code_exit, pay.date.year, pay.date.month)
                #pay.name = pay.journal_id.code_exit + pay.name[pay.name.find("/"):]
        
        return moves
    
    def _post(self, soft=True):
        if soft:
            future_moves = self.filtered(lambda move: move.date > fields.Date.context_today(self))
            future_moves.auto_post = True
            for move in future_moves:
                msg = _('This move will be posted at the accounting date: %(date)s', date=format_date(self.env, move.date))
                move.message_post(body=msg)
            to_post = self - future_moves
        else:
            to_post = self
        _logger.warning("+-------------------------------------+")
        _logger.warning([move.name for move in to_post])
        moves = super(AccountMove, self)._post(soft)
        for move in moves:
            statement_line = self.env["account.bank.statement.line"].search([("move_id", "=", move.id)], limit=1)
            _logger.warning(f"{statement_line.name}: {statement_line.amount}")
            if statement_line and statement_line.amount < 0 and move.journal_id.type == 'bank' and move.journal_id.code_exit:
                move._set_custom_move_sequence()        
        _logger.warning([move.name for move in moves])
        return moves
    
    def _set_custom_move_sequence(self):
        self.ensure_one()
        sequence_prefix = "%s/%04d/%02d/" % (self.journal_id.code_exit, self.date.year, self.date.month)
        last_sequence = self.env["account.move"].search([("name", "like", sequence_prefix)], limit=1, order="name desc")
        if not last_sequence:
            self.name = sequence_prefix + "0001"
            self.sequence_number = 1
        else:
            self.name = sequence_prefix + str(last_sequence.sequence_number + 1).zfill(4)
            self.sequence_number += 1