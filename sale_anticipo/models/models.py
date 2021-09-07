#-*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import UserError, RedirectWarning


class SaleOrder(models.Model):
    _inherit = 'sale.order'
#     _description = 'sale_anticipo.sale_anticipo'

    is_anticipo = fields.Boolean('Es un anticipo')
    factura_anticipo = fields.Many2one('account.move', 'Factura Amortización', domain= "['&',('is_anticipo','=',True),('journal_id.type','=','sale'),('partner_id','=', partner_id)]")

#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))

        invoice_vals = {
            'ref': self.client_order_ref or '',
            'move_type': 'out_invoice',
            'narration': self.note,
            'currency_id': self.pricelist_id.currency_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'source_id': self.source_id.id,
            'invoice_user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(self.partner_invoice_id.id)).id,
            'partner_bank_id': self.company_id.partner_id.bank_ids[:1].id,
            'journal_id': self.warehouse_id.journal_id.id,  # company comes from the journal
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'payment_reference': self.reference,
            'transaction_ids': [(6, 0, self.transaction_ids.ids)],
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
            'is_anticipo': self.is_anticipo,
            'factura_anticipo': self.factura_anticipo.id,
            

        }
        return invoice_vals

class AccountMove(models.Model):
    _inherit = 'account.move'

    is_anticipo = fields.Boolean('Es un anticipo')
    factura_anticipo = fields.Many2one('account.move', 'Factura Amortización',domain=[('journal_id.type','=',"sale")])


    #@api.model
    def saldo_pendiente(self):        

        #for order in self:
        model = self.env['account.move']
        invoices = model.search([('payment_state','in',('in_payment','paid','reversed','partial')),('factura_anticipo','=',self.id)])

        saldo = 0
        for inv in invoices:
            invoices_reverse = self.env['account.move'].search([('reversed_entry_id','=',inv.id)])
            for inv_r in invoices_reverse:
                if inv_r.l10n_mx_edi_payment_method_id.code == '30':
                    saldo += inv_r.amount_total
        
        saldo_pendiente = self.amount_total - saldo

        if (saldo_pendiente != 0):
            msg = _("""El saldo pendiente para esta Factura de Anticipo es: $%s""") % round(saldo_pendiente, 2)
            raise UserError(_('Factura de Anticipo') + '\n' + msg)
        else:
            raise UserError('No existe saldo pendiente para esta factura')

