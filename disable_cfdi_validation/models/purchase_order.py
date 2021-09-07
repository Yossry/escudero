# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def action_create_invoice(self):
        """Create the invoice associated to the PO. """
        if not self.xml_edi and not self.partner_id.disable_cfdi_validation:
            raise UserError('No puede crear la factura sin adjuntar el XML')
        
        res = super(PurchaseOrder, self).action_create_invoice()
        return res