# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools import float_compare, date_utils, email_split, email_re
from odoo.tools.misc import formatLang, format_date, get_lang
import warnings
from lxml import etree
from lxml.objectify import fromstring
import base64


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_mx_validate_uuid = fields.Char('Folio Fiscal', readonly=True)
    xml_valido = fields.Boolean(help='Verifica que la factura sea valida en base al XML adjuntos', default=False)
    xml_edi = fields.Binary('XML de Factura', attachment=True)
    file_name = fields.Char("File Name")

    def action_validar_facturas(self):
        self.xml_valido = False

        def get_node(cfdi_node, attribute, namespaces):
            if hasattr(cfdi_node, 'Complemento'):
                node = cfdi_node.Complemento.xpath(attribute, namespaces=namespaces)
                return node[0] if node else None
            else:
                return None

        cfdi_data = base64.decodebytes(self.xml_edi)
        cfdi_node = fromstring(cfdi_data)
        tfd_node = get_node(
            cfdi_node,
            'tfd:TimbreFiscalDigital[1]',
            {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'},
        )

        uuid = tfd_node.get('UUID' , '')
        supplier_rfc = cfdi_node.Emisor.get('Rfc', cfdi_node.Emisor.get('rfc'))
        stamp_date = tfd_node.get('FechaTimbrado', '').replace('T', ' ')
        serie = cfdi_node.get('Serie', '')
        folio = cfdi_node.get('Folio', '')
        total = cfdi_node.get('Total', '')
        currency = cfdi_node.get('Moneda', '')
        folio_factura = serie + folio
        total_invoice = 53.63


        model = self.env['account.move']
        lista = model.search([('move_type','=','in_invoice'),('state','in',('draft','posted')),('l10n_mx_validate_uuid','=',uuid)])

        for item in lista:            
            raise UserError('Factura Invalida: EL Folio Fiscal ya ha sido registrado, verifique los documentos publicados o en estado borrador.')
      
        if(self.partner_id.vat != supplier_rfc):
            raise UserError('Factura Invalida, verifique el XML adjuntado: El RFC no corresponde')
        if(self.amount_total != float(total)):
            raise UserError('Factura Invalida, verifique el XML adjuntado: Los importes no corresponden')
        if(self.currency_id.name != currency):
            raise UserError('Factura Invalida, verifique el XML adjuntado: La moneda de la factura no corresponde con el XML')
        
        self.ref = folio_factura
        self.l10n_mx_validate_uuid = uuid
        self.date = stamp_date
        self.invoice_date = stamp_date
        self.xml_valido = True


    def action_post(self):        
        
        for order in self:
            for line in self.line_ids:
                    if not line.analytic_account_id:
                        cuenta_analitica =self.line_ids[0].analytic_account_id
                        line.write({'analytic_account_id': cuenta_analitica })
                        
            if (self.move_type == 'in_invoice'):                
                cuenta_analitica =self.line_ids[0].analytic_account_id
                for line in self.line_ids:
                    if line.analytic_account_id != cuenta_analitica:
                        raise UserError('No se pueden ingresar cuentas analiticas diferentes')

                if not self.xml_valido:
                    raise UserError('No se ha validado el XML, de clic en Validar XML')
                
            

        
        
        return self._post(soft=False)
    
        

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }


    xml_edi = fields.Binary('XML de Factura', attachment=True)
    file_name = fields.Char("File Name")

    def _prepare_invoice(self):
        """Prepare the dict of values to create the new invoice for a purchase order.
        """
        self.ensure_one()
        move_type = self._context.get('default_move_type', 'in_invoice')
        journal = self.env['account.move'].with_context(default_move_type=move_type)._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))

        partner_invoice_id = self.partner_id.address_get(['invoice'])['invoice']
        invoice_vals = {
            'ref': self.partner_ref or '',
            'move_type': move_type,
            'narration': self.notes,
            'currency_id': self.currency_id.id,
            'invoice_user_id': self.user_id and self.user_id.id,
            'journal_id': self.picking_type_id.warehouse_id.journal_id_supplier.id,
            'partner_id': partner_invoice_id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(partner_invoice_id)).id,
            'payment_reference': self.partner_ref or '',
            'partner_bank_id': self.partner_id.bank_ids[:1].id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': [],
            'company_id': self.company_id.id,
            'xml_edi': self.xml_edi,
            'file_name': self.file_name,
        }
        return invoice_vals

    

    @api.constrains('xml_edi')
    def _check_file(self):
        if self.xml_edi:
            if str(self.file_name.split(".")[1]) != 'xml' :
                raise UserError("No puede adjuntar un archivo que no sea XML")

    def button_confirm(self):
        for order in self:
            current_login= self.env.user
            if self.amount_total > current_login.amount_purchase_approval_max:
                raise UserError('No puede validar esta orden: Limite de aprobacion superado')
            #Solo una cuenta análitica por pedido
            cuenta_analitica =self.order_line[0].account_analytic_id.id
            for line in self.order_line:
                if line.account_analytic_id.id != cuenta_analitica:
                    raise UserError('No se puede generar una pedido con diferentes cuentas analiticas. Verifique que la cuenta análitica sea la misma para todas las lineas del pedido')
            
            #Cuentas análiticas permitidas por almacén
            lista = []
            cuentas_perm =self.picking_type_id.warehouse_id.analytic_account_ids    
            for item in cuentas_perm:
                lista.append(item.id)

            existe = cuenta_analitica not in lista

            if existe:
                raise UserError('Seleccione el Almacen de recepción correspondiente a la cuenta cuenta analitica')

            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step'\
                    or (order.company_id.po_double_validation == 'two_step'\
                        and order.amount_total < self.env.company.currency_id._convert(
                            order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()))\
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True

    def action_create_invoice(self):
        """Create the invoice associated to the PO. """
        # if not self.xml_edi:
        #         raise UserError('No puede crear la factura sin adjuntar el XML')
        
        res = super(PurchaseOrder, self).action_create_invoice()
        return res

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    account_analytic_id = fields.Many2one('account.analytic.account', store=True, string='Analytic Account', compute='_compute_analytic_id_and_tag_ids', readonly=False, required=True)

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', index=True, compute="_compute_analytic_account", store=True, readonly=False, check_company=True, copy=True, required=False)


    

        

