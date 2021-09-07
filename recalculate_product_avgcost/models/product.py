# -*- coding: utf-8 -*-
##############################################################################
#
#    SIE CENTER custom module for Odoo
#    Copyright (C) 2021
#    @author: @cyntiafelix
#
##############################################################################

from odoo import api, fields, models
from odoo.tools import float_is_zero
from odoo.exceptions import Warning, ValidationError
import dateutil.parser

class SIECenter_ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_recalculate_avgcost(self):
        total = 0
        total_success = 0
        total_errors = 0
        error_list = []
        for product_template in self:
            success, log = product_template.product_variant_id.recalculate_avgcost()
            product_template.message_post(body = ("<br/>").join(log))
            total += 1
            if success:
                total_success += 1
            else:
                total_errors += 1
                error_list.append(log[-1])

        message_list = [("Total registros modificados: %s / %s"%(total_success, total))]
        if total_errors:
            message_list.append("Total registros sin modificar: %s / %s"%(total_errors, total))
            message_list.extend(error_list)

        message_id = self.env['message.window'].create({'message':  ('\n').join(message_list)})
        return {
            'name': 'Recalcular Costo Promedio',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'message.window',
            # pass the id
            'res_id': message_id.id,
            'target': 'new'
        }


class SIECenter_Product(models.Model):
    _inherit = 'product.product'

    def action_recalculate_avgcost(self):
        total = 0
        total_success = 0
        total_errors = 0
        error_list = []
        for product in self:
            success, log = product.recalculate_avgcost()
            product.message_post(body = ("<br/>").join(log))
            total += 1
            if success:
                total_success += 1
            else:
                total_errors += 1
                error_list.append(log[-1])

        message_list = [("Total registros modificados: %s / %s"%(total_success, total))]
        if total_errors:
            message_list.append("Total registros sin modificar: %s / %s"%(total_errors, total))
            message_list.extend(error_list)

        message_id = self.env['message.window'].create({'message':  ('\n').join(message_list)})
        return {
            'name': 'Recalcular Costo Promedio',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'message.window',
            # pass the id
            'res_id': message_id.id,
            'target': 'new'
        }


    def recalculate_avgcost(self):
        self.ensure_one()
        log = []
        log.append("RECALCULO DE COSTO PROMEDIO Y VALUACION DE INVENTARIO")

        #Action applies only for average cost method
        if self.cost_method not in ('average'):
            log.append("El método de costo %s para el producto %s no aplica a esta acción"%(self.cost_method, self.name))
            return False, log

        #Searching move lines for the product sorted by date and status done
        stock_move_lines = self.env['stock.move.line'].search(
                            ['&', ('product_id', '=', self.id), ('state', '=', 'done')], order='date')
        if len(stock_move_lines) <= 0:
            log.append("El producto %s no cuenta con movimientos para esta acción"%self.name)
            return False, log
        stock_moves = [move.move_id.id for move in stock_move_lines]

        #Deleting all valuation lines for the product and move lines
        log.append("Las siguientes líneas de valoración y contabilidad fueron eliminadas")
        valuation_lines = self.env['stock.valuation.layer'].search(
                            ['&', ('product_id', '=', self.id), ('stock_move_id', 'in', stock_moves)])
        account_moves_ids = []
        for valuation in valuation_lines:
            if (valuation.account_move_id):
                account_moves_ids.append(valuation.account_move_id.id)
            log.append("--------------------------------------------------")
            log.append('Movimiento de Inventario (referencia): %s'%valuation.stock_move_id.reference)
            log.append("Valoración Inventario: %s"%(valuation.description))
            log.append("Asiento Contable: %s"%(valuation.account_move_id.name))
        valuation_lines.sudo().unlink()

        #Unreconcile account moves before deleting
        account_moves = self.env['account.move'].search([('id', 'in', account_moves_ids)])
        for account_move in account_moves:
            if account_move.has_reconciled_entries:
                for account_line in account_move.line_ids:
                    if (account_line.reconciled or account_line.matching_number):
                        reconcile_ids = [line.id for line in account_line.full_reconcile_id]
                        credit_ids = [line.id for line in account_line.matched_credit_ids]
                        debit_ids = [line.id for line in account_line.matched_debit_ids]
                        if len(reconcile_ids) > 0:
                            search_lines = self.env['account.full.reconcile'].search([('id', 'in', reconcile_ids)])
                            reconcile_lines = [line.reconciled_line_ids for line in search_lines]
                        elif len(credit_ids) > 0:
                            search_lines = self.env['account.partial.reconcile'].search([('id', 'in', credit_ids)])
                            reconcile_lines = [line.credit_move_id for line in search_lines]
                        elif len(debit_ids) > 0:
                            search_lines = self.env['account.partial.reconcile'].search([('id', 'in', debit_ids)])
                            reconcile_lines = [line.debit_move_id for line in search_lines]
                        for lines in reconcile_lines:
                            log.append("--------------------------------------------------")
                            log.append("Asientos Contables desconciliados: %s"%(', ').join([line.move_id.name for line in lines]))
                            lines.remove_move_reconcile()

        #Deleting account moves for the product
        account_moves._context['force_delete'] = True
        account_moves.sudo().unlink()

        log.append("<br/>")

        #Ensure that move lines got force date if exists
        for move_line in stock_move_lines:
            move = move_line.move_id
            force_date = move.picking_id.force_date
            if force_date:
                final_date = dateutil.parser.parse(str(force_date)).date()
            else:
                final_date = self._context.get('force_period_date', move.date)
            if move_line.date != final_date:
                move_line.with_company(move.company_id.id).sudo().write({'date': final_date})

        #Creating new valuation layer for each move line in status Done
        log.append("Las siguientes transferencias fueron revaloradas siguiendo el orden de su fecha")
        sorted(stock_move_lines, key=lambda m: m.date)
        for move_line in stock_move_lines:
            if move_line.state != 'done':
                continue
            move = move_line.move_id
            rounding = move.product_id.uom_id.rounding
            diff = move_line.qty_done
            if float_is_zero(diff, precision_rounding=rounding):
                continue

            log.append("--------------------------------------------------")
            log.append("Referencia: %s"%move_line.reference)
            log.append("Estado: %s"%move_line.state)
            log.append("Fecha: %s"%move_line.date)
            if move._is_in():
                log.append("Tipo Movimiento: Entrada")
            elif move._is_out():
                log.append("Tipo Movimiento: Salida")
            log.append("Cantidad: %s"%diff)
            log.append("Precio Unitario: %s"%move._get_price_unit())
            move_line.sudo()._create_correction_svl(move, diff)

        return True, log

class SIECenter_MessageWindow(models.TransientModel):
    _name = 'message.window'

    message = fields.Text('Message', required=True)

    def action_ok(self):
        """ close window"""
        return {'type': 'ir.actions.act_window_close'}
