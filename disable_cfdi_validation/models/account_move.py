# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.exceptions import UserError
from lxml.objectify import fromstring
import base64


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_validar_facturas(self):
        self.ensure_one()
        if self.partner_id.disable_cfdi_validation:
            raise UserError('El usuario seleccionado no requiere validar factura')
        return super(AccountMove, self).action_validar_facturas()

    def action_post(self):
        for order in self:
            for line in order.line_ids:
                    if not line.analytic_account_id:
                        cuenta_analitica = order.line_ids[0].analytic_account_id
                        line.write({'analytic_account_id': cuenta_analitica })
                        
            if order.move_type == 'in_invoice':                
                cuenta_analitica = order.line_ids[0].analytic_account_id
                for line in order.line_ids:
                    if line.analytic_account_id != cuenta_analitica:
                        raise UserError('No se pueden ingresar cuentas analiticas diferentes')

                if not order.xml_valido and not order.partner_id.disable_cfdi_validation:
                    raise UserError('No se ha validado el XML, de clic en Validar XML')
                
        return self._post(soft=False)