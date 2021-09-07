# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    add_analytic_acc_tag = fields.Boolean(string="Cuenta analitica en pago", default=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string="Cuenta análitica")
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string="Analytic Tags")

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        result = super(AccountPayment, self)._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)
        tags = [tag.id for tag in self.analytic_tag_ids]
        if self.add_analytic_acc_tag:
            for move_line in result:
                move_line.update({
                    'analytic_account_id': self.analytic_account_id.id,
                    'analytic_tag_ids':[(6,0,tags)]
                })   
        return result

    
    def action_post(self):
        result = super(AccountPayment, self).action_post()
        account_move = self.move_id
        tags = [tag.id for tag in self.analytic_tag_ids]
        if self.add_analytic_acc_tag:
            for invoice_line in account_move.invoice_line_ids:
                invoice_line.update({
                    'analytic_account_id':self.analytic_account_id.id,
                    'analytic_tag_ids':[(6,0,tags)]
                })
        return result


class MyAccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    add_analytic_acc_tag = fields.Boolean(string="Cuenta analitica en pago", default=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string="Cuenta análitica")
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string="Analytic Tags")

    
    def _create_payment_vals_from_wizard(self):
        result = super(MyAccountPaymentRegister, self)._create_payment_vals_from_wizard()
        tags = [tag.id for tag in self.analytic_tag_ids]
        if self.add_analytic_acc_tag:
            result.update({
                'add_analytic_acc_tag': True,
                'analytic_account_id':self.analytic_account_id.id,
                'analytic_tag_ids':[(6,0,tags)]
            })
        return result

    def _create_payment_vals_from_batch(self):
        result = super(MyAccountPaymentRegister, self)._create_payment_vals_from_batch()
        tags = [tag.id for tag in self.analytic_tag_ids]
        if self.add_analytic_acc_tag:
            result.update({
                'add_analytic_acc_tag': True,
                'analytic_account_id':self.analytic_account_id.id,
                'analytic_tag_ids':[(6,0,tags)]
            })
        return result

class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"

    @api.model
    def _prepare_cash_basis_tax_line_vals(self, tax_line, balance, amount_currency):
        ''' Prepare the move line corresponding to a tax in the cash basis entry.

        :param tax_line:        An account.move.line record being a tax line.
        :param balance:         The balance to consider for this line.
        :param amount_currency: The balance in foreign currency to consider for this line.
        :return:                A python dictionary that could be passed to the create method of
                                account.move.line.
        '''
        account_analytic_id = tax_line.analytic_account_id.id
        return {
            'name': tax_line.name,
            'debit': balance if balance > 0.0 else 0.0,
            'credit': -balance if balance < 0.0 else 0.0,
            'tax_base_amount': tax_line.tax_base_amount,
            'tax_repartition_line_id': tax_line.tax_repartition_line_id.id,
            'tax_ids': [(6, 0, tax_line.tax_ids.ids)],
            'tax_tag_ids': [(6, 0, tax_line._convert_tags_for_cash_basis(tax_line.tax_tag_ids).ids)],
            'account_id': tax_line.tax_repartition_line_id.account_id.id or tax_line.account_id.id,
            'amount_currency': amount_currency,
            'currency_id': tax_line.currency_id.id,
            'partner_id': tax_line.partner_id.id,
            'tax_exigible': True,
            'analytic_account_id': account_analytic_id,
        }

    @api.model
    def _prepare_cash_basis_counterpart_tax_line_vals(self, tax_line, cb_tax_line_vals):
        ''' Prepare the move line used as a counterpart of the line created by
        _prepare_cash_basis_tax_line_vals.

        :param tax_line:            An account.move.line record being a tax line.
        :param cb_tax_line_vals:    The result of _prepare_cash_basis_counterpart_tax_line_vals.
        :return:                    A python dictionary that could be passed to the create method of
                                    account.move.line.
        '''
        account_analytic_id = tax_line.analytic_account_id.id
        return {
            'name': cb_tax_line_vals['name'],
            'debit': cb_tax_line_vals['credit'],
            'credit': cb_tax_line_vals['debit'],
            'account_id': tax_line.account_id.id,
            'amount_currency': -cb_tax_line_vals['amount_currency'],
            'currency_id': cb_tax_line_vals['currency_id'],
            'partner_id': cb_tax_line_vals['partner_id'],
            'tax_exigible': True,
            'analytic_account_id': account_analytic_id,
        }



class accline(models.Model):
    _inherit = "account.move.line"

    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")
    