# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import Warning
import datetime


class PagoTerceroWizard(models.TransientModel):
    _name = "wizard.pago_terceros"

    partner_id = fields.Many2one(
        string="Proveedor de Tarjeta de Crédito",
        comodel_name="res.partner", required=True)
        #domain=[('type','=','product')])
    journal_id = fields.Many2one(
        string="Diario",
        comodel_name="account.journal",       
        domain=[('type','=','general')],required=True)

    

    def generate(self):
        """Crea un asiento contable de reclasificación"""
        self.ensure_one()
        format = "%Y-%m-%d"
        move_ids = self.env['account.move'].browse(self.env.context['active_ids'])
        today = datetime.datetime.today()
        date = today.strftime(format)


        for move in move_ids:
            default_line_name = _('Pago por cuenta tercero %s', move.name)
            move.apply_pago_tercero = True
            move.proveedor_pago_tercero = self.partner_id
            amount = move.amount_total
            analytic_account_id= move.line_ids[0].analytic_account_id.id
            

            line_vals_list = [{'name': default_line_name,
            'date_maturity': date,
            'debit': amount,
            'currency_id': move.currency_id.id,
            'partner_id': move.partner_id.id,
            'account_id': move.partner_id.property_account_payable_id.id,
            'analytic_account_id': analytic_account_id
            },
                # Receivable / Payable.
            {'name': default_line_name,
            'date_maturity': date,
            'credit': amount,
            'currency_id': move.currency_id.id,
            'partner_id': self.partner_id.id,
            'account_id': self.partner_id.property_account_payable_id.id,
            'analytic_account_id': analytic_account_id
            },]

            movess = {
                'ref': 'Pago por Aplicación de Terceros'+ ' - ' + str(move.name),
                'partner_id': self.partner_id.id,      
                'journal_id': self.journal_id.id,
                'date': date,
                'currency_id': move.currency_id.id,

            }

                        
            
            if move.move_type in 'in_invoice' and move.state in 'posted' and move.payment_state not in ('in_payment','paid','reversed'):
                
                move_id = self.env['account.move'].sudo().with_context(default_move_type='entry').create(movess)
                
                for i, pay in enumerate(move_id):
                    
                    to_write = []
                    
                    for line_vals in line_vals_list:
                        to_write.append((0, 0, line_vals))


                    pay.write({'line_ids': to_write})
                    pay.write({'state': 'posted'})
            else:
                raise Warning('Solo se puede aplicar pago por Terceros a Facturas de Proveedor no Pagadas')

            



    