from odoo import models, fields, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    #is_credit_card = fields.Boolean('Tarjeta de Crédito',default=False)

class Expense(models.Model):
    _inherit = 'hr.expense'

    partner_id = fields.Many2one('res.partner', 'Proveedor',required=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', check_company=True, required=True)
    pagado_credito = fields.Boolean('Pagado Tarjeta de Crédito')
    tarjeta_credito = fields.Many2one('res.partner', 'Tarjeta de Crédito', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")#,('is_credit_card', '=', True)

    def _get_account_move_line_values(self):
    #	res = super(HrExpense, self)._get_account_move_line_values()
        move_line_values_by_expense = {}
        for expense in self:
            move_line_name = expense.employee_id.name + ': ' + expense.name.split('\n')[0][:64]
            account_src = expense._get_expense_account_source()
            account_dst = expense._get_expense_account_destination()
            account_date = expense.sheet_id.accounting_date or expense.date or fields.Date.context_today(expense)

            company_currency = expense.company_id.currency_id

            move_line_values = []
            taxes = expense.tax_ids.with_context(round=True).compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id)
            total_amount = 0.0
            total_amount_currency = 0.0
            partner = expense.partner_id.id
            if expense.pagado_credito:
                partner_employee = expense.tarjeta_credito.id
            else:
                partner_employee = expense.employee_id.sudo().address_home_id.commercial_partner_id.id
            

            # source move line
            balance = expense.currency_id._convert(taxes['total_excluded'], company_currency, expense.company_id, account_date)
            amount_currency = taxes['total_excluded']
            move_line_src = {
                'name': move_line_name,
                'quantity': expense.quantity or 1,
                'debit': balance if balance > 0 else 0,
                'credit': -balance if balance < 0 else 0,
                'amount_currency': amount_currency,
                'account_id': account_src.id,
                'product_id': expense.product_id.id,
                'product_uom_id': expense.product_uom_id.id,
                'analytic_account_id': expense.analytic_account_id.id,
                'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)],
                'expense_id': expense.id,
                'partner_id': partner,
                'tax_ids': [(6, 0, expense.tax_ids.ids)],
                'tax_tag_ids': [(6, 0, taxes['base_tags'])],
                'currency_id': expense.currency_id.id,
            }
            move_line_values.append(move_line_src)
            total_amount -= balance
            total_amount_currency -= move_line_src['amount_currency']

            # taxes move lines
            for tax in taxes['taxes']:
                balance = expense.currency_id._convert(tax['amount'], company_currency, expense.company_id, account_date)
                amount_currency = tax['amount']

                if tax['tax_repartition_line_id']:
                    rep_ln = self.env['account.tax.repartition.line'].browse(tax['tax_repartition_line_id'])
                    base_amount = self.env['account.move']._get_base_amount_to_display(tax['base'], rep_ln)
                else:
                    base_amount = None

                move_line_tax_values = {
                    'name': tax['name'],
                    'quantity': 1,
                    'debit': balance if balance > 0 else 0,
                    'credit': -balance if balance < 0 else 0,
                    'amount_currency': amount_currency,
                    'account_id': tax['account_id'] or move_line_src['account_id'],
                    'tax_repartition_line_id': tax['tax_repartition_line_id'],
                    'tax_tag_ids': tax['tag_ids'],
                    'tax_base_amount': base_amount,
                    'expense_id': expense.id,
                    'partner_id': partner,
                    'currency_id': expense.currency_id.id,
                    'analytic_account_id': expense.analytic_account_id.id if tax['analytic'] else False,
                    #'analytic_account_id': expense.analytic_account_id.id,
                    'analytic_tag_ids': [(6, 0, expense.analytic_tag_ids.ids)] if tax['analytic'] else False,
                }
                total_amount -= balance
                total_amount_currency -= move_line_tax_values['amount_currency']
                move_line_values.append(move_line_tax_values)

            # destination move line
            move_line_dst = {
                'name': move_line_name,
                'debit': total_amount > 0 and total_amount,
                'credit': total_amount < 0 and -total_amount,
                'account_id': account_dst,
                'date_maturity': account_date,
                'amount_currency': total_amount_currency,
                'currency_id': expense.currency_id.id,
                'expense_id': expense.id,
                'partner_id': partner_employee,
                'analytic_account_id': expense.analytic_account_id.id
            }
            move_line_values.append(move_line_dst)

            move_line_values_by_expense[expense.id] = move_line_values
        return move_line_values_by_expense


    def _get_expense_account_destination(self):
        self.ensure_one()
        account_dest = self.env['account.account']
        if self.payment_mode == 'company_account':
            if not self.sheet_id.bank_journal_id.payment_credit_account_id:
                raise UserError(_("No Outstanding Payments Account found for the %s journal, please configure one.") % (self.sheet_id.bank_journal_id.name))
            account_dest = self.sheet_id.bank_journal_id.payment_credit_account_id.id
        else:
            if not self.employee_id.sudo().address_home_id:
                raise UserError(_("No Home Address found for the employee %s, please configure one.") % (self.employee_id.name))
            
            if self.pagado_credito:
                partner = self.tarjeta_credito
                account_dest = partner.property_account_payable_id.id or partner.parent_id.property_account_payable_id.id
            else:
                partner = self.employee_id.sudo().address_home_id.with_company(self.company_id)
                account_dest = partner.property_account_payable_id.id or partner.parent_id.property_account_payable_id.id
            return account_dest

    def action_get_attachment_view(self):
        self.ensure_one()
        #res = self.env['ir.actions.act_window']._for_xml_id('hr_expense.hr_expense_view_form') #base.action_attachment
        #res['domain'] = [('res_model', '=', 'hr.expense'), ('res_id', 'in', self.ids)]
        #res['context'] = {'default_res_model': 'hr.expense', 'default_res_id': self.id}
        #return res
        return {
            'name': _('Expense'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.expense',
            'target': 'current',
            'res_id': self.id,
        }
        
