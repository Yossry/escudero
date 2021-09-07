# -*-coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools import date_utils
import io
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter

import logging
_logger = logging.getLogger(__name__)

def get_products_and_move_ordered(self, location_id, start, end, filter_by,
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
    moves = self.env['stock.move'].search(moves_domain, order="product_reference asc, date desc")
    _logger.warning("---------------------------------------")
    _logger.warning("Stock card report")
    _logger.warning("---------------------------------------")

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

def get_line_sn(mvl_in_pro, mvl_out_pro, is_zero, location_id, start, end, lot, product, price):
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

    line_sn['si'] = actual_qty - tot_in + tot_out
    line_sn['in'] = tot_in
    line_sn['out'] = tot_out
    line_sn['bal'] = tot_in - tot_out
    line_sn['fi'] = actual_qty
    line_sn['cost'] = price
    line_sn['value'] = price * actual_qty

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

    products, mv_in, mv_out, quants = get_products_and_move_ordered(
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
    datas['filter_category'] = data['category_name']
    datas['show_cost'] = show_cost

    datas['filter_title_label'] = ""
    datas['filter_title_value'] = ""
    if filter_by == 'product' and filter_products:
        datas['filter_title_label'] = "Filter Products"
        datas['filter_title_value'] = data['products_name']
    elif filter_by == 'category' and category_id:
        datas['filter_title_label'] = "Filter Categories"
        datas['filter_title_value'] = data['category_name']

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

        for product in products_categ.sorted(lambda r: r.default_code):
            line = {}
            line['name'] = product.name
            line['ref'] = product.default_code
            line['uom'] = product.uom_id.name
            line['lines'] = []

            # get the price
            company = self._context.get('force_company', self.env.user.company_id.id)
            price = product.standard_price#get_history_price(company, end)
            
            mv_in_pro = mv_in.filtered(
                lambda x: x.product_id.id == product.id)
            mv_out_pro = mv_out.filtered(
                lambda x: x.product_id.id == product.id)
            quants_pro = quants.filtered(
                lambda x: x.product_id.id == product.id)

            lots = quants_pro.mapped('lot_id')
            lots |= mv_in_pro.mapped("move_line_ids.lot_id")
            lots |= mv_out_pro.mapped("move_line_ids.lot_id")

            mvl_in_pro = mv_in_pro.mapped("move_line_ids")
            mvl_out_pro = mv_out_pro.mapped("move_line_ids")


            if group_by_serial and product.tracking:
                for lot in lots:

                    mvl_in_lot = mv_in_pro.mapped("move_line_ids").filtered(
                        lambda x: x.lot_id.id == lot.id)
                    mvl_out_lot = mv_out_pro.mapped("move_line_ids").filtered(
                        lambda x: x.lot_id.id == lot.id)
                    elt = get_line_sn(
                        mvl_in_lot, mvl_out_lot, is_zero, location_id, start, end, lot, product, price)
                    if elt:
                        line['lines'].append(elt)

                # get the value stock of product with no lot
                rem_si = sum([x['si'] for x in line['lines']])
                rem_in = sum([x['in'] for x in line['lines']])
                rem_out = sum([x['out'] for x in line['lines']])
                rem_bal = sum([x['bal'] for x in line['lines']])
                rem_fi = sum([x['fi'] for x in line['lines']])
                rem_val = sum([x['value'] for x in line['lines']])
                no_lot_line = get_line_sn(
                    mvl_in_pro, mvl_out_pro, is_zero, location_id, start, end, None, product, price)
                if no_lot_line:
                    no_lot_line['si'] -= rem_si
                    no_lot_line['in'] -= rem_in
                    no_lot_line['out'] -= rem_out
                    no_lot_line['bal'] -= rem_bal
                    no_lot_line['fi'] -= rem_fi
                    no_lot_line['value'] -= rem_val
                    if no_lot_line['si'] or no_lot_line['bal'] or no_lot_line['fi']:
                        elt['origin'] = mvl_in_pro[0].picking_id.origin or mvl_in_pro[0].move_id.origin or "-"
                        line['lines'].append(no_lot_line)
            else:
                elt = get_line_sn(
                    mvl_in_pro, mvl_out_pro, is_zero, location_id, start, end, None, product, price)
                if elt:
                    elt['origin'] = mvl_in_pro[0].picking_id.origin or mvl_in_pro[0].move_id.origin or "-"
                    line['lines'].append(elt)

            line_categ['lines'].append(line)
        result.append(line_categ)

    datas['lines'] = result
    return datas


def get_excel_file(self, data):

    # cree le document
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})

    return workbook, output


class StockCardReport(models.AbstractModel):
    _inherit = 'report.hyd_stock_card.stock_card_template'

    def _get_report_values(self, docids, data=None):
        location = self.env['stock.location'].browse(data['location_id'])
        company = location.company_id or self.env.company.id
        return {'doc_ids': docids, 'data': get_values(self, data), 'company': company}


class StockCardReportLandscape(models.AbstractModel):
    _inherit = 'report.hyd_stock_card.stock_card_template_landscape'

    def _get_report_values(self, docids, data=None):
        location = self.env['stock.location'].browse(data['location_id'])
        company = location.company_id or self.env.company.id
        return {'doc_ids': docids, 'data': get_values(self, data), 'company': company}


class StockCardReportXls(models.AbstractModel):
    _inherit = 'report.hyd_stock_card.stock_card_report_xls.xlsx'

    def generate_xlsx_report(self, workbook, data, lines):
        sheet = workbook.add_worksheet('Stock Card')
        format0 = workbook.add_format({'font_size': 20, 'align': 'center', 'bold': True})
        format1 = workbook.add_format({'font_size': 14, 'align': 'vcenter', 'bold': True})
        format1_nobold = workbook.add_format({'font_size': 14, 'align': 'vcenter', 'bold': False})
        format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'bold': True})
        format21 = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': True})
        format21_nobold = workbook.add_format({'font_size': 10, 'align': 'left', 'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        format4 = workbook.add_format({'font_size': 12, 'align': 'left', 'bold': True})
        font_size_8 = workbook.add_format({'font_size': 8, 'align': 'center'})
        font_size_8_l = workbook.add_format({'font_size': 8, 'align': 'left'})
        font_size_8_r = workbook.add_format({'font_size': 8, 'align': 'right'})
        red_mark = workbook.add_format({'font_size': 8, 'bg_color': 'red'})
        justify = workbook.add_format({'font_size': 12})
        format3.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')

        format_tab_entete = workbook.add_format({'font_size': 10, 'align': 'center', 'bold': True})
        format_tab_entete.set_bg_color('#333333')
        format_tab_entete.set_font_color('white')
        format_tab_entete.set_align('center')

        sheet.merge_range(2, 1, 2, 2, 'Warehouse', format21)
        sheet.merge_range(2, 3, 2, 4, data['warehouse'], format21_nobold)

        if data['filter_title_label']:
            sheet.write(3, 1, 'Location', format21)
            sheet.merge_range(3, 2, 3, 3, data['location'], format21_nobold)
            sheet.write(3, 4, data['filter_title_label'], format21)
            sheet.merge_range(3, 5, 3, 6, data['filter_title_value'], format21_nobold)
        else:
            sheet.merge_range(3, 1, 3, 3, 'Location', format21)
            sheet.merge_range(3, 4, 3, 5, data['location'], format21_nobold)

        sheet.write(4, 1, 'Date from', format21)
        sheet.write(4, 2, data['date_from'], format21_nobold)
        sheet.write(4, 3, 'Date to', format21)
        sheet.write(4, 4, data['date_to'], format21_nobold)

        sheet.write(6, 1, 'Reference', format_tab_entete)
        sheet.write(6, 2, 'Designation', format_tab_entete)
        sheet.write(6, 3, 'Uom', format_tab_entete)
        index = 4
        if data['show_cost']:
            sheet.write(6, index, 'Cost', format_tab_entete)
            index += 1
        if data['group_by_serial']:
            sheet.write(6, index, 'S/N', format_tab_entete)
            index += 1
        sheet.write(6, index, 'Stock initial', format_tab_entete)
        sheet.write(6, index + 1, 'In', format_tab_entete)
        sheet.write(6, index + 2, 'Out', format_tab_entete)
        sheet.write(6, index + 3, 'Balance', format_tab_entete)
        sheet.write(6, index + 4, 'Final stock', format_tab_entete)
        if data['show_cost']:
            sheet.write(6, index + 5, 'Value', format_tab_entete)

        i = 7

        for categ in data['lines']:

            if categ['show']:
                sheet.merge_range(i, 1, i, 2, "Category", font_size_8_l)
                sheet.merge_range(i, 3, i, 10, categ['name'], format21)
                i += 1

            for line in categ['lines']:

                length = len(line['lines'])
                if length == 0:
                    continue
                if length == 1:
                    sheet.write(i, 1, line['ref'], font_size_8_l)
                    sheet.write(i, 2, line['name'], font_size_8_l)
                    sheet.write(i, 3, line['uom'], font_size_8_l)
                elif length > 1:
                    sheet.merge_range(i, 1, i + length - 1, 1, line['ref'], font_size_8_l)
                    sheet.merge_range(i, 2, i + length - 1, 2, line['name'], font_size_8_l)
                    sheet.merge_range(i, 3, i + length - 1, 3, line['uom'], font_size_8_l)

                for line_sn in line['lines']:
                    index = 4
                    if data['show_cost']:
                        sheet.write(i, index, line_sn['cost'], font_size_8_r)
                        index += 1
                    if data['group_by_serial']:
                        sheet.write(i, index, line_sn['name'], font_size_8_r)
                        index += 1
                    sheet.write(i, index, line_sn['si'], font_size_8_r)
                    sheet.write(i, index + 1, line_sn['in'], font_size_8_r)
                    sheet.write(i, index + 2, line_sn['out'], font_size_8_r)
                    sheet.write(i, index + 3, line_sn['bal'], font_size_8_r)
                    sheet.write(i, index + 4, line_sn['fi'], font_size_8_r)
                    if data['show_cost']:
                        sheet.write(i, index + 5, line_sn['value'], font_size_8_r)
                    i += 1
