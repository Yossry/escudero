# -*- coding: utf-8 -*-

from odoo import api, fields, models, _



class ResPartner(models.Model):
    _inherit = 'res.partner'

    #@api.multi
    def _uninvoiced_total_amount_get(self):
        sale_data = self.env['sale.order'].read_group(
            domain=[('partner_id', 'child_of', self.ids),('state','=','sale'),('invoice_status','in',['to invoice', 'no'])],
            fields=['amount_total'], 
            groupby=['partner_id'])

        partner_child_ids = self.read(['child_ids'])
        mapped_data = dict([(m['partner_id'][0], m['amount_total']) for m in sale_data])


        for partner in self:
            item = next(p for p in partner_child_ids if p['id'] == partner.id)
                
            partner_ids = [partner.id] + item.get('child_ids')
            partner.uninvoiced_total_amount = sum(mapped_data.get(child, 0) for child in partner_ids)

    uninvoiced_total_amount = fields.Monetary(compute='_uninvoiced_total_amount_get', 
        string='Total Uninvoiced Amount', help="Total uninvoiced amount this customer owes you.")

    apply_individual_credit_limit = fields.Boolean(string='Crédito individual', default=False)
    credit_limit = fields.Monetary(string='Crédito Limite', default=0.0, tracking=True)
    #credit_card = fields.Boolean(string='Tarjeta de Crédito', default=False)
