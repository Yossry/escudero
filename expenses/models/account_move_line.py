from odoo import models, api, fields

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.onchange('partner_id')
    def _compute_account_id_expense(self):
        self.ensure_one()
        move_type = self.move_id.move_type
        account_id_expense = self.partner_id.property_account_payable_id

        if move_type in 'in_invoice':
            self.account_id = account_id_expense

        #raise Warning('Asegurese que esta modificando el Contacto de la linea del proveedor antes de validar')

    


    