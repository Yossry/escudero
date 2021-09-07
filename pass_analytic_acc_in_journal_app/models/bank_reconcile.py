# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import float_is_zero
from odoo.tools import float_compare, float_round, float_repr
from odoo.tools.misc import formatLang, format_date
from odoo.exceptions import UserError, ValidationError

import time
import math
import base64
import re

class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    def button_validate(self):

        ca = self.line_ids.move_id.line_ids[1].analytic_account_id
        for line in self.line_ids:
            for item in line.move_id.line_ids:
                item.analytic_account_id = ca

        if any(statement.state != 'posted' or not statement.all_lines_reconciled for statement in self):
            raise UserError(_('All the account entries lines must be processed in order to validate the statement.'))

        for statement in self:

            # Chatter.
            statement.message_post(body=_('Statement %s confirmed.', statement.name))

            # Bank statement report.
            if statement.journal_id.type == 'bank':
                content, content_type = self.env.ref('account.action_report_account_statement')._render(statement.id)
                self.env['ir.attachment'].create({
                    'name': statement.name and _("Bank Statement %s.pdf", statement.name) or _("Bank Statement.pdf"),
                    'type': 'binary',
                    'datas': base64.encodebytes(content),
                    'res_model': statement._name,
                    'res_id': statement.id
                })

        self.write({'state': 'confirm', 'date_done': fields.Datetime.now()})

    def button_validate_or_action(self):
        
        for line in self.line_ids:            
            for item in line.move_id.line_ids:
                ids = item._reconciled_lines()
                for l in ids:
                    ac = self.env['account.move.line'].search([('id','=', l)])
                    if ac.analytic_account_id:
                        analytic_account_id = ac.analytic_account_id.id
                        item.analytic_account_id = analytic_account_id
                #item.update('analytic_account_id': analytic_account_id)


        if self.journal_type == 'cash' and not self.currency_id.is_zero(self.difference):
            action_rec = self.env['ir.model.data'].xmlid_to_object('account.action_view_account_bnk_stmt_check')
            if action_rec:
                action = action_rec.read()[0]
                return action

        return self.button_validate()
