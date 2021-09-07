# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF, float_compare
from odoo.addons import decimal_precision as dp


class SaleOrder(models.Model):
    _inherit = "sale.order"

    #state = fields.Selection(selection_add=[('waiting_for_payment', 'Aprobación Pago')])
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('waiting_for_approval', 'Aprobación Descuento'),
        ('waiting_for_payment', 'Aprobación Pago'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account',
    readonly=True, copy=False, check_company=True,  # Unrequired company
    states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
    domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    help="The analytic account related to a sales order.", required=True)

    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', check_company=True, #Unrequired company
    domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", readonly=True)
    #Order's type
    type_order = fields.Selection([
        ('amortizacion', 'Amortización'),
        ('price_change', 'Cambio de Precio'),
        ('change_product', 'Cambio de Producto'),], string='Tipo de Pedido')

    @api.onchange('warehouse_id')
    def _onchange_analytic(self):
        # !!! Any change to the default value may have to be repercuted
        # on _init_column() below.
        self.analytic_account_id = self.warehouse_id.analytic_account_id.id

    #@api.multi
    def action_confirm(self):
        Params = self.env['ir.config_parameter'].sudo()

        on_exceeded = Params.get_param('partner_credit_limit.on_exceeded') or False
        use_global_limit = Params.get_param('partner_credit_limit.use_global_limit') or False
        global_limit = float(Params.get_param('partner_credit_limit.global_limit')) or 0.0
        include_uninvoiced = Params.get_param('partner_credit_limit.include_uninvoiced') or True

        for order in self:
            this_credit_limit = this_credit_to_compare = 0.0
            #Check if this_partner has a parent entity.
            #If id does, move to parent anyway.
            this_partner = order.partner_id.parent_id or order.partner_id

            #Credit limit with partner first if we apply_individual_credit_limit on this partner. 
            if this_partner.apply_individual_credit_limit:
                this_credit_limit = this_partner.credit_limit

            #See if we use a global credit limit.
            if use_global_limit:
                #Credit limit go with the global limit.
                this_credit_limit = global_limit


            #The amount we compare credit to.
            this_credit_to_compare = order.amount_total


            #See if we count in the uninvoiced amount.
            if include_uninvoiced:
                this_credit_to_compare += this_partner.uninvoiced_total_amount

            #Count in credit in account app this partner already has.
            #this_credit_to_compare += this_partner.credit
            this_credit_to_compare += this_partner.total_overdue

            #Credits do exceeded.

            if this_credit_limit > 0 and this_credit_to_compare > this_credit_limit:
                if on_exceeded == 'raise_exception':
                    #We raise exception
                    credit = this_credit_limit - (this_credit_to_compare - order.amount_total)
                    msg = _("""Se excedió el credito del cliente. Credito disponible: $%s.""") % round(credit, 2)
                    raise UserError(_('Limite de crédito excedido') + '\n' + msg)

                elif on_exceeded == 'leave_undecided':
                    order.write({'state': 'account_review'})
            else:
                #Do normal stuff.
                #raise UserError(order.type_order)

                if not order.type_order:
                    if (order.payment_term_id.id == 1):
                        order.write({'state': 'waiting_for_payment'}) 
                    else:
                        super(SaleOrder, order).action_confirm()                       
                else:
                    super(SaleOrder, order).action_confirm()

        
        return True


    def action_payment_approve(self):
        for order in self:
            super(SaleOrder, order).action_confirm()


    #@api.multi
    def action_account_approve(self):
        for order in self:
            if(order.partner_id.apply_individual_credit_limit):
                super(SaleOrder, order).action_confirm()
            else:
                order.write({'state': 'waiting_for_payment'})

    #@api.multi
    def action_account_disapprove(self):
        self.filtered(lambda s: s.state == 'account_review').write({'state': 'draft'})
        return True