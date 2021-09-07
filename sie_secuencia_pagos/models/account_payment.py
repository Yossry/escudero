# -*- coding: utf-8 -*-
from odoo import api, models
import logging
_logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
    #_inherit = ['account.payment', 'account.move', 'sequence.mixin']
    _inherit = 'account.payment'

    @api.model_create_multi
    def create(self, vals_list):
        payments = super(AccountPayment, self).create(vals_list)
        for pay in payments:
            if pay.payment_type == "outbound" and pay.journal_id.type == 'bank' and pay.journal_id.code_exit:
                pay._set_custom_payment_sequence()
                #pay.sequence_prefix = "%s/%04d/%02d/" % (pay.journal_id.code_exit, pay.date.year, pay.date.month)
                #pay.name = pay.journal_id.code_exit + pay.name[pay.name.find("/"):]
        
        return payments
    
    def _set_custom_payment_sequence(self):
        self.ensure_one()
        sequence_prefix = "%s/%04d/%02d/" % (self.journal_id.code_exit, self.date.year, self.date.month)
        last_sequence = self.env["account.move"].search([("name", "like", sequence_prefix)], limit=1, order="name desc")
        if not last_sequence:
            self.name = sequence_prefix + "0001"
            self.sequence_number = 1
        else:
            _logger.warning("---------------------------------------")
            _logger.warning(last_sequence.sequence_prefix + " - " + str(last_sequence.sequence_number))
            self.name = sequence_prefix + str(last_sequence.sequence_number + 1).zfill(4)
            self.sequence_number += 1
    
    # @api.depends('posted_before', 'state', 'journal_id', 'date')
    # def _compute_name(self):
    #     super(AccountPayment, self)._compute_name()
    #     _logger.warning("---------------------------------------")
    #     _logger.warning(self.sequence_prefix)

    # def _get_starting_sequence(self):
    #     self.ensure_one()
    #     _logger.warning("---------------------------------------")
    #     _logger.warning("get sequence")
    #     starting_sequence = super(AccountPayment, self)._get_starting_sequence()
    #     # if self.payment_type == "outbound" and self.journal_id.type == 'bank' and self.journal_id.code_exit:
    #     #     code = self.journal_id.code_exit
    #     #     starting_sequence = "%s/%04d/%02d/0000" % (code, self.date.year, self.date.month)
    #     return starting_sequence
    
    # def _get_last_sequence_domain(self, relaxed=False):
    #     where_string, param = super(AccountPayment, self)._get_last_sequence_domain(relaxed)
    #     _logger.warning("---------------------------------------")
    #     _logger.warning(self.sequence_prefix)
    #     return where_string, param
    