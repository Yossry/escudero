# -*-coding: utf-8 -*-
from odoo import api, fields, models, _
from openerp.exceptions import Warning
from datetime import datetime
import pytz
from odoo.tools import date_utils
import io
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

FORMAT_DATE = "%Y-%m-%d"
ERREUR_FUSEAU = _("Set your timezone in preferences")



def convert_UTC_TZ(self, UTC_datetime):
    if not self.env.user.tz:
        raise Warning(ERREUR_FUSEAU)
    local_tz = pytz.timezone(self.env.user.tz)
    date = UTC_datetime
    date = pytz.utc.localize(date, is_dst=None).astimezone(local_tz)
    return date.strftime(FORMAT_DATE)

def get_products_and_move(self, location_id, start, end, filter_by,
                              filter_products, category_id):
    quant_obj = self.env["stock.quant"]

    # domains
    quant_domain = [('location_id', 'child_of', location_id)]
    moves_domain = [
        ('date', '>=', start),
        ('date', '<=', end),
        ('state', '=', 'done'),
        '|',
        ('location_dest_id', 'child_of', location_id),
        ('location_id', 'child_of', location_id)]

    if filter_by == 'product' and filter_products:
        quant_domain.append(('product_id', 'in', filter_products))
        moves_domain.append(('product_id', 'in', filter_products))

    elif filter_by == 'category' and category_id:
        quant_domain.append(('product_id.categ_id', 'child_of', category_id))
        moves_domain.append(('product_id.categ_id', 'child_of', category_id))

    quants = quant_obj.search(quant_domain)
    moves = self.env['stock.move'].search(moves_domain)

    location = self.env['stock.location'].browse(location_id)
    location_ids = self.env['stock.location'].search([
        ('parent_path', '=like', location.parent_path + "%")])

    mv_in = moves.filtered(
        lambda x: x.location_dest_id.id in location_ids.ids)
    mv_out = moves.filtered(
        lambda x: x.location_id.id in location_ids.ids)

    products = quants.mapped('product_id')
    products |= mv_in.mapped("product_id")
    products |= mv_out.mapped("product_id")

    return (products, mv_in, mv_out, quants)

def get_line_sn(self, mvl_in_pro, mvl_out_pro, is_zero, location_id, start, end, lot, product, company, lots_to_exclude=None):
    line_sn = {}
    line_sn['name'] = lot.name if lot else ""

    if not is_zero and not mvl_in_pro and not mvl_out_pro:
        return None

    product_uom = product.uom_id
    tot_in = 0
    for elt in mvl_in_pro:
        if product_uom.id != elt.product_uom_id.id:
            factor = product_uom.factor / elt.product_uom_id.factor
        else:
            factor = 1.0
        tot_in += elt.qty_done * factor

    tot_out = 0
    for elt in mvl_out_pro:
        if product_uom.id != elt.product_uom_id.id:
            factor = product_uom.factor / elt.product_uom_id.factor
        else:
            factor = 1.0
        tot_out += elt.qty_done * factor

    ctx = {
        'location': location_id,
        'to_date': end}
    if lot:
        ctx['lot_id'] = lot.id
    actual_qty = product.with_context(ctx).qty_available
    price_start = product.standard_price#get_history_price(company, start)
    #price_start = product.get_history_price(company, start)
    price_end = product.standard_price#get_history_price(company, end)

    # get the qty of tracking product without lot
    if not lot and lots_to_exclude:
        actual_qty_lots = 0
        for lot_exc in lots_to_exclude:
            ctx = {
                'location': location_id,
                'to_date': end}
            if lot_exc:
                ctx['lot_id'] = lot_exc.id
            actual_qty_lots += product.with_context(ctx).qty_available
        actual_qty -= actual_qty_lots

    line_sn['si'] = actual_qty - tot_in + tot_out
    line_sn['in'] = tot_in
    line_sn['out'] = tot_out
    line_sn['bal'] = tot_in - tot_out
    line_sn['fi'] = actual_qty
    line_sn['cost_si'] = price_start
    line_sn['cost_fi'] = price_end
    line_sn['value_si'] = price_start * (actual_qty - tot_in + tot_out)
    line_sn['value_fi'] = price_end * actual_qty

    location = self.env['stock.location'].browse(location_id)
    location_ids = self.env['stock.location'].search([
        ('parent_path', '=like', location.parent_path + "%")])

    move_to_show = self.env['stock.move.line']
    move_to_show |= mvl_in_pro
    move_to_show |= mvl_out_pro
    move_to_show = move_to_show.sorted(lambda r: r.date)
    line_sn['lines'] = []
    val_in = actual_qty - tot_in + tot_out
    val_fin = val_in
    for mvl in move_to_show:

        src = mvl.location_id.id
        dst = mvl.location_dest_id.id
        qty = mvl.qty_done

        val_in = qty if dst in location_ids.ids else 0
        val_out = qty if src in location_ids.ids else 0
        val_bal = val_in - val_out
        val_fin += val_bal

        mvdate = convert_UTC_TZ(self, mvl.date) if mvl.date else ""
        mvname = mvl.picking_id.name or mvl.move_id.name or "-"
        price = 0

        if mvl.stock_valuation_layer_ids:
            if mvl.product_uom_qty > 0:            
                price = mvl.stock_valuation_layer_ids[0].unit_cost
            

        #get_history_price(company, mvl.date)

        elt = {}
        elt['mv'] = mvname
        elt['date'] = str(mvdate) or "-"
        elt['in'] = val_in
        elt['out'] = val_out
        elt['bal'] = val_bal
        elt['fi'] = val_fin
        elt['cost'] = price
        elt['value'] = val_bal * price
        line_sn['lines'].append(elt)

    return line_sn

def get_line(self, mv_in_pro, mv_out_pro, is_zero, location_id, start, end, product, company):
    line_sn = {}
    line_sn['name'] = ""

    if not is_zero and not mv_in_pro and not mv_out_pro:
        return None

    product_uom = product.uom_id
    tot_in = 0
    for elt in mv_in_pro:
        if product_uom.id != elt.product_uom.id:
            factor = product_uom.factor / elt.product_uom.factor
        else:
            factor = 1.0
        tot_in += elt.product_uom_qty * factor

    tot_out = 0
    for elt in mv_out_pro:
        if product_uom.id != elt.product_uom.id:
            factor = product_uom.factor / elt.product_uom.factor
        else:
            factor = 1.0
        tot_out += elt.product_uom_qty * factor

    ctx = {
        'location': location_id,
        'to_date': end}
    actual_qty = product.with_context(ctx).qty_available
    price_start = product.standard_price
    #get_history_price(company, start)
    price_end = product.standard_price#get_history_price(company, end)

    line_sn['si'] = actual_qty - tot_in + tot_out
    line_sn['in'] = tot_in
    line_sn['out'] = tot_out
    line_sn['bal'] = tot_in - tot_out
    line_sn['fi'] = actual_qty
    line_sn['cost_si'] = price_start
    line_sn['cost_fi'] = price_end
    line_sn['value_si'] = price_start * (actual_qty - tot_in + tot_out)
    line_sn['value_fi'] = price_end * actual_qty

    location = self.env['stock.location'].browse(location_id)
    location_ids = self.env['stock.location'].search([
        ('parent_path', '=like', location.parent_path + "%")])

    move_to_show = self.env['stock.move']
    move_to_show |= mv_in_pro
    move_to_show |= mv_out_pro
    move_to_show = move_to_show.sorted(lambda r: r.date)
    line_sn['lines'] = []
    val_in = actual_qty - tot_in + tot_out
    val_fin = val_in
    for mv in move_to_show:

        src = mv.location_id.id
        dst = mv.location_dest_id.id
        qty = mv.product_uom_qty

        val_in = qty if dst in location_ids.ids else 0
        val_out = qty if src in location_ids.ids else 0
        val_bal = val_in - val_out
        val_fin += val_bal

        mvdate = convert_UTC_TZ(self, mv.date) if mv.date else ""
        #mvname = mv.picking_id.name or mv.name or "-"
        if mv.picking_id.note:          
            mvname = str(mv.reference) + " - " + str(mv.picking_id.note)
        else:
            mvname = str(mv.reference)
        price = 0
        if mv.stock_valuation_layer_ids:
            if mv.product_uom_qty > 0:            
                price = mv.stock_valuation_layer_ids[0].unit_cost
        #get_history_price(company, mv.date)

        elt = {}
        elt['mv'] = mvname
        elt['date'] = str(mvdate) or "-"
        elt['in'] = val_in
        elt['out'] = val_out
        elt['bal'] = val_bal
        elt['fi'] = val_fin
        elt['cost'] = price
        elt['value'] = val_bal * price
        line_sn['lines'].append(elt)

    return line_sn

def get_values(self, data):
    quant_obj = self.env["stock.quant"]
    products = self.env['product.product']

    start= data['start']
    start = str(start) + ' 00:00:00'
    end = data['end'] 
    end = str(end) + ' 23:59:59'
    date_start = data['date_start'] 
    date_start = str(date_start) + ' 00:00:00'
    date_end = data['date_end']
    date_end = str(date_end) + ' 23:59:59'
    location_id = data['location_id']
    category_id = data['category_id']
    filter_products = data['products']
    is_zero = data['is_zero']
    filter_by = data['filter_by']
    group_by_category = data['group_by_category']
    group_by_serial = data['group_by_serial']
    show_cost = data['show_cost']

    products, mv_in, mv_out, quants = get_products_and_move(
        self, location_id, start, end, filter_by,
        filter_products, category_id)

    datas = {}
    datas['warehouse'] = data['warehouse_name']
    datas['location'] = data['location_name']
    datas['date_from'] = date_start
    datas['date_to'] = date_end
    datas['details'] = data['details']
    datas['group_by_category'] = data['group_by_category']
    datas['group_by_serial'] = data['group_by_serial']
    datas['show_cost'] = show_cost

    # title filter
    datas['filter_title_label'] = ""
    datas['filter_title_value'] = ""
    if filter_by == 'product' and filter_products:
        datas['filter_title_label'] = "Productos"
        datas['filter_title_value'] = data['products_name']
    elif filter_by == 'category' and category_id:
        datas['filter_title_label'] = "Categorías"
        datas['filter_title_value'] = data['category_name']

    result = []
    categories = products.mapped('categ_id')

    result = []
    categories = products.mapped('categ_id')

    for categ in categories:
        line_categ = {}
        line_categ['name'] = categ.name
        line_categ['lines'] = []

        if group_by_category:
            products_categ = products.filtered(
                lambda x: x.categ_id.id == categ.id)
            line_categ['show'] = True
        else:
            products_categ = products
            products -= products_categ
            line_categ['show'] = False

        for product in products_categ.sorted(lambda r: r.name):
            line = {}
            line['name'] = product.name
            line['ref'] = product.default_code
            line['uom'] = product.uom_id.name
            line['lines'] = []

            mv_in_pro = mv_in.filtered(
                lambda x: x.product_id.id == product.id)
            mv_out_pro = mv_out.filtered(
                lambda x: x.product_id.id == product.id)
            quants_pro = quants.filtered(
                lambda x: x.product_id.id == product.id)

            number_line_pro = 0

            # get the price
            company = self._context.get('force_company', self.env.user.company_id.id)
            price = product.standard_price#get_history_price(company, end)

            if group_by_serial and product.tracking:

                lots = quants_pro.mapped('lot_id')
                lots |= mv_in_pro.mapped("move_line_ids.lot_id")
                lots |= mv_out_pro.mapped("move_line_ids.lot_id")

                for lot in lots:
                    mvl_in_pro = mv_in_pro.mapped("move_line_ids")
                    mvl_out_pro = mv_out_pro.mapped("move_line_ids")

                    mvl_in_lot = mv_in_pro.mapped("move_line_ids").filtered(
                        lambda x: x.lot_id.id == lot.id)
                    mvl_out_lot = mv_out_pro.mapped("move_line_ids").filtered(
                        lambda x: x.lot_id.id == lot.id)
                    elt = get_line_sn(
                        self, mvl_in_lot, mvl_out_lot, is_zero, location_id, start, end, lot, product, company)
                    if elt:
                        line['lines'].append(elt)
                        number_line_pro += len(elt['lines']) + 2

                # for stock tracking without lot or s/n
                mvl_in_lot = mv_in_pro.mapped("move_line_ids").filtered(
                        lambda x: not x.lot_id)
                mvl_out_lot = mv_out_pro.mapped("move_line_ids").filtered(
                    lambda x: not x.lot_id)
                elt = get_line_sn(
                        self, mvl_in_lot, mvl_out_lot, is_zero, location_id,
                        start, end, None, product, company, lots)
                if elt:
                    line['lines'].append(elt)
                    number_line_pro += len(elt['lines']) + 2
            else:
                
                elt = get_line(self, mv_in_pro, mv_out_pro, is_zero, location_id, start, end, product, company)
                if elt:
                    line['lines'].append(elt)
                    number_line_pro += len(elt['lines']) + 2
            line['number_line'] = number_line_pro

            line_categ['lines'].append(line)
        result.append(line_categ)

    datas['lines'] = result
    return datas


class StockCardDetailsReport(models.AbstractModel):
    _name = 'report.hyd_stock_card.stock_card_details_template'

    def _get_report_values(self, docids, data=None):

        return {'doc_ids': docids, 'data': get_values(self, data)}


class StockCardDetailsReportXls(models.AbstractModel):
    _name = 'report.hyd_stock_card.stock_card_details_report_xls.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):

        sheet = workbook.add_worksheet('Reporte KARDEX')
        format0 = workbook.add_format({'font_size': 20, 'align': 'center', 'bold': True})
        format1 = workbook.add_format({'font_size': 14, 'align': 'vcenter', 'bold': True})
        format1_nobold = workbook.add_format({'font_size': 14, 'align': 'vcenter', 'bold': False})
        format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})
        format21 = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': True})
        format21_nobold = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        format4 = workbook.add_format({'font_size': 12, 'align': 'left', 'bold': True})
        font_size_8 = workbook.add_format({'font_size': 8, 'align': 'center'})
        font_size_8_l = workbook.add_format({'font_size': 8, 'align': 'center', 'bold': True})
        font_size_8_r = workbook.add_format({'font_size': 8, 'align': 'right'})
        font_size_8_blue = workbook.add_format({'font_size': 8, 'align': 'right', 'bg_color': '#95A5A6'})
        font_size_8_bold = workbook.add_format({'font_size': 8, 'align': 'right', 'bold': True})
        red_mark = workbook.add_format({'font_size': 8, 'bg_color': 'red'})
        justify = workbook.add_format({'font_size': 12})
        format3.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')
        font_size_8_l.set_align('vcenter')

        format_tab_entete = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True})
        format_tab_entete.set_bg_color('#333333')
        format_tab_entete.set_font_color('white')
        format_tab_entete.set_align('center')

        sheet.merge_range(1, 1, 1, 12, 'REPORTE KARDEX DE INVENTARIO', format_tab_entete)

        sheet.merge_range(2, 1, 2, 3, 'Almacen', format21)
        sheet.merge_range(2, 4, 2, 12, data['warehouse'], format21_nobold)

        if data['filter_title_label']:
            sheet.write(3, 1, 'Ubicación', format21)
            sheet.merge_range(3, 2, 3, 3, data['location'], format21_nobold)
            sheet.write(3, 4, data['filter_title_label'], format21)
            sheet.merge_range(3, 5, 3, 12, data['filter_title_value'], format21_nobold)
        else:
            sheet.merge_range(3, 1, 3, 3, 'Ubicación', format21)
            sheet.merge_range(3, 4, 3, 5, data['location'], format21_nobold)

        sheet.write(4, 1, 'Desde', format21)
        sheet.merge_range(4, 2, 4, 3, data['date_from'], format21_nobold)
        sheet.write(4, 4, 'Hasta', format21)
        sheet.merge_range(4, 5, 4, 6, data['date_to'], format21_nobold)

        sheet.write(6, 1, 'Referencia', format_tab_entete)
        sheet.write(6, 2, 'Producto', format_tab_entete)
        sheet.write(6, 3, 'UdM', format_tab_entete)
        index = 4
    #    if data['show_cost']:
    #        sheet.write(6, index, 'Costo', format_tab_entete)
    #        index += 1
        if data['group_by_serial']:
            sheet.write(6, index, 'S/N', format_tab_entete)
            index += 1
        sheet.write(6, index, 'Fecha', format_tab_entete)
        sheet.write(6, index + 1, 'Concepto', format_tab_entete)
        sheet.write(6, index + 2, 'Inicial', format_tab_entete)
        sheet.write(6, index + 3, 'Entradas', format_tab_entete)
        sheet.write(6, index + 4, 'Salidas', format_tab_entete)
        sheet.write(6, index + 5, 'Costo', format_tab_entete)
        sheet.write(6, index + 6, 'Valor', format_tab_entete)
        sheet.write(6, index + 7, 'Balance', format_tab_entete)
        sheet.write(6, index + 8, 'Final', format_tab_entete)
        #if data['show_cost']:
        #    sheet.write(6, index + 7, 'Valor', format_tab_entete)

        i = 7
        for categ in data['lines']:

            if categ['show']:
                sheet.merge_range(i, 1, i, 3, "Categoría", format_tab_entete)
                sheet.merge_range(i, 4, i, 12, categ['name'], format21)
                i += 1

            for line in categ['lines']:

                length = len(line['lines'])
                if length == 0:
                    continue

                sheet.merge_range(i, 1, i + line['number_line'] - 1, 1, line['ref'], font_size_8_l)
                sheet.merge_range(i, 2, i + line['number_line'] - 1, 2, line['name'], font_size_8_l)
                sheet.merge_range(i, 3, i + line['number_line'] - 1, 3, line['uom'], font_size_8_l)

                compt = 0
                for line_sn in line['lines']:
                    compt += 1
                    index = 4
                #    if data['show_cost']:
                #        sheet.write(i, index, line_sn['cost_si'], font_size_8_r)
                #        index += 1
                    if data['group_by_serial']:
                        length = len(line_sn['lines']) + 2
                        sheet.write(i, index + 2, line_sn['si'], font_size_8_blue)
                        sheet.merge_range(i, index, i + length - 1, index, line_sn['name'], font_size_8_r)
                        index += 1
                    else:
                        sheet.write(i, index + 2, line_sn['si'], font_size_8_blue)

                #    if data['show_cost']:
                #        sheet.write(i, index + 7, line_sn['value_si'], font_size_8_bold)
                    i += 1

                    for sline in line_sn['lines']:
                        if data['show_cost']:
                            offset = 1
                            if data['group_by_serial']:
                                offset += 1
                            sheet.write(i, index - offset , sline['cost'], font_size_8_r)
                        sheet.write(i, index, sline['date'], font_size_8_r)
                        sheet.write(i, index + 1, sline['mv'], font_size_8_r)
                        sheet.write(i, index + 3, sline['in'], font_size_8_r)
                        sheet.write(i, index + 4, sline['out'], font_size_8_r)
                        sheet.write(i, index + 5, sline['cost'], font_size_8_r)
                        sheet.write(i, index + 6, sline['value'], font_size_8_r)
                        sheet.write(i, index + 7, sline['bal'], font_size_8_r)
                        sheet.write(i, index + 8, sline['fi'], font_size_8_r)
                    #    if data['show_cost']:
                    #        sheet.write(i, index + 7, sline['value'], font_size_8_r)
                        i += 1

                    sheet.write(i, index + 8, line_sn['fi'], font_size_8_blue)
                    if data['show_cost']:
                        offset = 1
                        if data['group_by_serial']:
                            offset += 1
                        #sheet.write(i, index - offset , line_sn['cost_fi'], font_size_8_r)
                        #sheet.write(i, index + 7, line_sn['value_fi'], font_size_8_bold)
                    i += 1
