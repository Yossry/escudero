# -*- coding: utf-8 -*-

from odoo import fields, models, exceptions

from odoo.exceptions import UserError, ValidationError

class ResUsers(models.Model):
    _inherit = 'res.users'

    amount_purchase_approval_min = fields.Float('Monto minimo Compras')
    amount_purchase_approval_max = fields.Float('Monto máximo Compras')
    purchase_order_can_approve = fields.Boolean('Aprobador de Compras')

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	def button_approve(self, force=False):

		"""if not self.user_id.purchase_order_can_approve:
			raise ValidationError('Restricciones de Usuario: Sin permisos para validar PO')"""

		if self.amount_total < self.user_id.amount_purchase_approval_min or self.amount_total > self.user_id.amount_purchase_approval_max:
			raise exceptions.ValidationError('No puede validar esta orden: Limite de aprobacion superado')			
		else:
			return super(PurchaseOrder, self).button_approve(force=force)
		

	
	