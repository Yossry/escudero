# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import base64
from io import StringIO
from odoo import api, fields, models
from datetime import date
from odoo.tools.float_utils import float_round
from odoo.exceptions import Warning


import io
try:
    import xlwt
except ImportError:
    xlwt = None

class sale_day_book_wizard(models.TransientModel):
    _name = "sale.day.book.wizard"
    
    start_date = fields.Date('Start Period', required=True)
    end_date = fields.Date('End Period', required=True)
    warehouse = fields.Many2many('stock.warehouse', 'wh_wiz_rel_inv_val', 'wh', 'wiz', string='Warehouse')
    category = fields.Many2many('product.category', 'categ_wiz_rel', 'categ', 'wiz' , domain = [('property_valuation','=','real_time')])
    location_id = fields.Many2one('stock.location', string= 'Location')
    company_id = fields.Many2one('res.company', string= 'Company', default=lambda self: self.env['res.company']._company_default_get('account.move'))
    display_sum = fields.Boolean("Summary")
    filter_by = fields.Selection([('product','Product'),('categ','Category')],string="Filter By",default = "product")
    product_ids = fields.Many2many('product.product', 'rel_product_val_wizard', string="Product", domain = [('type','=','product')])
    

    def print_report(self):
        datas = {
            'ids': self._ids,
            'model': 'sales.day.book.wizard',
            'start_date':self.start_date,
            'end_date':self.end_date,
            'warehouse':self.warehouse,
            'company_id':self.company_id,
            'display_sum':self.display_sum,
            'product_ids': self.product_ids,
            'filter_by' : self.filter_by
            }
        return self.env.ref('bi_inventory_valuation_reports.inventory_product_category_template_pdf').report_action(self)
    
    def get_warehouse(self):
        if self.warehouse:
            l1 = []
            l2 = []
            for i in self.warehouse:
                obj = self.env['stock.warehouse'].search([('id', '=', i.id)])
                for j in obj:
                    l2.append(j.id)
            return l2
        return []
    
    def _get_warehouse_name(self):
        if self.warehouse:
            l1 = []
            l2 = []
            for i in self.warehouse:
                obj = self.env['stock.warehouse'].search([('id', '=', i.id)])
                l1.append(obj.name)
                myString = ",".join(l1 )
            return myString
        return ''


    def get_company(self):
        
        if self.company_id:
            l1 = []
            l2 = []
            obj = self.env['res.company'].search([('id', '=', self.company_id.id)])
            l1.append(obj.name)
            return l1

    def get_currency(self):
        if self.company_id:
            l1 = []
            l2 = []
            obj = self.env['res.company'].search([('id', '=', self.company_id.id)])
            l1.append(obj.currency_id.name)
            return l1

    def get_category(self):
        if self.category:
            l2 = []
            obj = self.env['product.category'].search([('id', 'in', self.category)])
            for j in obj:
                l2.append(j.id)
            return l2
        return ''
    
    def get_date(self):
        date_list = []
        obj = self.env['stock.history'].search([('date', '>=', self.start_date),('date', '<=', self.end_date)])
        for j in obj:
            date_list.append(j.id)
        return date_list


    def _compute_quantities_product_quant_dic(self,lot_id, owner_id, package_id,from_date,to_date,product_obj,data):
        loc_list = []
        domain_quant_loc, domain_move_in_loc, domain_move_out_loc = product_obj._get_domain_locations()
        custom_domain = []
        if data['company_id']:
            obj = self.env['res.company'].search([('name', '=', data['company_id'])])
            
            custom_domain.append(('company_id','=',obj.id))

        if data['location_id'] :
            custom_domain.append(('location_id','=',data['location_id'].id))

        if data['warehouse'] :
            ware_check_domain = [a.id for a in data['warehouse']]
            locations = []
            for i in ware_check_domain:
                loc_ids = self.env['stock.warehouse'].search([('id','=',i)])
                locations.append(loc_ids.view_location_id.id)
                for i in loc_ids.view_location_id.child_ids :
                  locations.append(i.id)
                loc_list.append(loc_ids.lot_stock_id.id)
            custom_domain.append(('location_id','in',locations))

        domain_quant = [('product_id', 'in', product_obj.ids)] + domain_quant_loc + custom_domain
        dates_in_the_past = False
        if to_date and to_date < date.today():
            dates_in_the_past = True
        domain_move_in = [('product_id', 'in', product_obj.ids)] + domain_move_in_loc
        domain_move_out = [('product_id', 'in', product_obj.ids)] + domain_move_out_loc
        if lot_id is not None:
            domain_quant += [('lot_id', '=', lot_id)]
        if owner_id is not None:
            domain_quant += [('owner_id', '=', owner_id)]
            domain_move_in += [('restrict_partner_id', '=', owner_id)]
            domain_move_out += [('restrict_partner_id', '=', owner_id)]
        if package_id is not None:
            domain_quant += [('package_id', '=', package_id)]
        if dates_in_the_past:
            domain_move_in_done = list(domain_move_in)
            domain_move_out_done = list(domain_move_out)
        if from_date:
            domain_move_in += [('date', '>=', from_date)]
            domain_move_out += [('date', '>=', from_date)]
        if to_date:
            domain_move_in += [('date', '<=', to_date)]
            domain_move_out += [('date', '<=', to_date)]

        Move = self.env['stock.move']
        Quant = self.env['stock.quant']
        domain_move_in_todo = [('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available'))] + domain_move_in
        domain_move_out_todo = [('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available'))] + domain_move_out
        moves_in_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_in_todo, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
        moves_out_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_out_todo, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
        quants_res = dict((item['product_id'][0], item['quantity']) for item in Quant.read_group(domain_quant, ['product_id', 'quantity'], ['product_id'], orderby='id'))
        
        if dates_in_the_past:
            # Calculate the moves that were done before now to calculate back in time (as most questions will be recent ones)
            domain_move_in_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_in_done
            domain_move_out_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_out_done
            moves_in_res_past = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_in_done, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
            moves_out_res_past = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_out_done, ['product_id', 'product_qty'], ['product_id'], orderby='id'))

        res = dict()
        for product in product_obj.with_context(prefetch_fields=False):
            product_id = product.id
            rounding = product.uom_id.rounding
            res[product_id] = {}
            if dates_in_the_past:
                qty_available = quants_res.get(product_id, 0.0) - moves_in_res_past.get(product_id, 0.0) + moves_out_res_past.get(product_id, 0.0)
            else:
                qty_available = quants_res.get(product_id, 0.0)
            res[product_id]['qty_available'] = float_round(qty_available, precision_rounding=rounding)
            res[product_id]['incoming_qty'] = float_round(moves_in_res.get(product_id, 0.0), precision_rounding=rounding)
            res[product_id]['outgoing_qty'] = float_round(moves_out_res.get(product_id, 0.0), precision_rounding=rounding)
            res[product_id]['virtual_available'] = float_round(
                qty_available + res[product_id]['incoming_qty'] - res[product_id]['outgoing_qty'],
                precision_rounding=rounding)
        return res




    def get_lines(self, data):
            product_res = self.env['product.product'].search([('qty_available', '!=', 0),
                                                                ('type', '=', 'product'),

                                                                ])
            category_lst = []
            if data['category'] :
                for cate in data['category']:
                    if data['filter_by'] == 'categ':
                        if cate.id not in category_lst :
                           category_lst.append(cate.id)
                           
                        for child in  cate.child_id :
                            if child.id not in category_lst :
                                category_lst.append(child.id)
            if len(category_lst) > 0 :

                product_res = self.env['product.product'].search([('categ_id','in',category_lst),('qty_available', '!=', 0),('type', '=', 'product')])
                
            if data['product_ids'] and data['filter_by'] == 'product':
                product_res = data['product_ids']

            lines = []
            for product in  product_res :

                sales_value = 0.0

                incoming = 0.0
                opening = self._compute_quantities_product_quant_dic(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'),False,data['start_date'],product,data)

                custom_domain = []
                if data['company_id']:
                    obj = self.env['res.company'].search([('name', '=', data['company_id'])])
                    custom_domain.append(('company_id','=',obj.id))


                if data['warehouse'] :
                    warehouse_lst = [a.id for a in data['warehouse']]
                    custom_domain.append(('picking_id.picking_type_id.warehouse_id','in',warehouse_lst))

                ######################
                stock_move_line = self.env['stock.move'].search([
                    ('product_id','=',product.id),
                    ('date','>',data['start_date']),
                    ('date',"<=",data['end_date']),
                    ('state','=','done')
                    ] + custom_domain)
                #########################################
                for move in stock_move_line :
                    if move.picking_id.picking_type_id.code == "outgoing" :
                        if data['location_id'] :
                            locations_lst = [data['location_id'].id]
                            for i in data['location_id'].child_ids :
                                locations_lst.append(i.id)
                            if move.location_id.id in locations_lst :
                                sales_value = sales_value + move.product_uom_qty

                        else :
                            sales_value = sales_value + move.product_uom_qty
                    if move.picking_id.picking_type_id.code == "incoming" :
                        if data['location_id'] :
                            locations_lst = [data['location_id'].id]
                            for i in data['location_id'].child_ids :
                                locations_lst.append(i.id)
                            if move.location_dest_id.id in locations_lst :
                                incoming = incoming + move.product_uom_qty
                        else :
                            incoming = incoming + move.product_uom_qty
                stock_val_layer = self.env['stock.valuation.layer'].search([
                        ('product_id','=',product.id),
                        ('force_date','>=',data['start_date']),
                        ('force_date',"<=",data['end_date']),
                        
                        ] )

                cost = 0
                count = 0
                for layer in stock_val_layer :
                        if layer.stock_move_id.picking_id.picking_type_id.code == "incoming" :
                            cost = cost + layer.unit_cost
                            count = count + 1
                        if not layer.stock_move_id.picking_id :
                            cost = cost + layer.unit_cost
                            count = count + 1
                avg_cost = 0
                if count > 0 :
                    avg_cost = cost / count

                if not stock_val_layer and  avg_cost == 0:
                    avg_cost = product.standard_price 

                inventory_domain = [
                    ('date','>',data['start_date']),
                    ('date',"<",data['end_date'])
                    ]
                stock_pick_lines = self.env['stock.move'].search([('location_id.usage', '=', 'inventory'),('product_id.id','=',product.id)] + inventory_domain)
                stock_internal_lines = self.env['stock.move'].search([('location_id.usage', '=', 'internal'),('location_dest_id.usage', '=', 'internal'),('product_id.id','=',product.id)] + inventory_domain)
                stock_internal_lines_2 = self.env['stock.move'].search([('location_id.usage', '=', 'internal'),('location_dest_id.usage', '=', 'inventory'),('product_id.id','=',product.id)] + inventory_domain)
                adjust = 0
                internal = 0
                plus_picking = 0
                
                if stock_pick_lines:
                    for invent in stock_pick_lines:
                        adjust = invent.product_uom_qty
                        plus_picking = invent.id
                min_picking = 0
                if stock_internal_lines_2 :
                    for inter in stock_internal_lines_2:
                        plus_min = inter.product_uom_qty
                        min_picking = inter.id

                if plus_picking > min_picking :
                    picking_id = self.env['stock.move'].browse(plus_picking)
                    adjust = picking_id.product_uom_qty
                else :
                    picking_id = self.env['stock.move'].browse(min_picking)
                    adjust = -int(picking_id.product_uom_qty)
                if stock_internal_lines:
                    for inter in stock_internal_lines:
                        internal = inter.product_uom_qty
                ending_bal = opening[product.id]['qty_available'] - sales_value + incoming + adjust
                method = ''
                price_used = product.standard_price
                if product.categ_id.property_cost_method == 'average' :
                    method = 'Average Cost (AVCO)'
                    price_used = avg_cost 

                elif product.categ_id.property_cost_method == 'standard' :
                    method = 'Standard Price'
                    price_used = product.standard_price


                vals = {
                        'sku': product.default_code or '',
                        'name': product.name or '',
                        'category': product.categ_id.name or '' ,
                        'cost_price': price_used or 0,
                        'available':  0 ,
                        'virtual':   0,
                        'incoming': incoming or 0,
                        'outgoing':  adjust,
                        'net_on_hand':   ending_bal,
                        'total_value': ending_bal * price_used or 0,
                        'sale_value': sales_value or 0,
                        'purchase_value':  0,
                        'beginning': opening[product.id]['qty_available'] or 0,
                        'internal': internal,
                        'costing_method' : method,
                    }
                lines.append(vals)
            return lines

    
    def get_data(self,data):
        product_res = self.env['product.product'].search([('qty_available', '!=', 0),
                                                                ('type', '=', 'product'),

                                                                ])
        category_lst = []
        if data['category'] :
            for cate in data['category'] :
                if cate.id not in category_lst :
                   category_lst.append(cate.id)
                for child in  cate.child_id :
                    if child.id not in category_lst :
                        category_lst.append(child.id)
        if len(category_lst) > 0 :
            product_res = self.env['product.product'].search([('categ_id','in',category_lst),('qty_available', '!=', 0),('type', '=', 'product')])
        lines = []
        for product in  product_res :
            sales_value = 0.0
            incoming = 0.0
            opening = self._compute_quantities_product_quant_dic(self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'),False,data['start_date'],product,data)
            custom_domain = []
            if data['company_id']:
                obj = self.env['res.company'].search([('name', '=', data['company_id'])])
                custom_domain.append(('company_id','=',obj.id))
            if data['warehouse'] :
                warehouse_lst = [a.id for a in data['warehouse']]
                custom_domain.append(('picking_id.picking_type_id.warehouse_id','in',warehouse_lst))

            ####################
            stock_move_line = self.env['stock.move'].search([
                ('product_id','=',product.id),
                ('date','>',data['start_date']),
                ('date',"<=",data['end_date']),
                ('state','=','done')
                ] + custom_domain)
            ################################
            for move in stock_move_line :
                if move.picking_id.picking_type_id.code == "outgoing" :
                    if data['location_id'] :
                        locations_lst = [data['location_id'].id]
                        for i in data['location_id'].child_ids :
                            locations_lst.append(i.id)
                        if move.location_id.id in locations_lst :
                            sales_value = sales_value + move.product_uom_qty
                    else :
                        sales_value = sales_value + move.product_uom_qty

                if move.picking_id.picking_type_id.code == "incoming" :
                    if data['location_id'] :
                        locations_lst = [data['location_id'].id]
                        for i in data['location_id'].child_ids :
                            locations_lst.append(i.id)
                        if move.location_dest_id.id in locations_lst :
                            incoming = incoming + move.product_uom_qty
                    else :
                        incoming = incoming + move.product_uom_qty
            stock_val_layer = self.env['stock.valuation.layer'].search([
                    ('product_id','=',product.id),
                    ('force_date','>=',data['start_date']),
                    ('force_date',"<=",data['end_date']),
                    
                    ] )

            cost = 0
            count = 0
            for layer in stock_val_layer :
                    if layer.stock_move_id.picking_id.picking_type_id.code == "incoming" :
                        cost = cost + layer.unit_cost
                        count = count + 1

                    if not layer.stock_move_id.picking_id :
                        cost = cost + layer.unit_cost
                        count = count + 1

            avg_cost = 0
            if count > 0 :
                avg_cost = cost / count

            if not stock_val_layer and  avg_cost == 0:
                avg_cost = product.standard_price 
                
            inventory_domain = [
                ('date','>',data['start_date']),
                ('date',"<",data['end_date'])
                ]
            stock_pick_lines = self.env['stock.move'].search([('location_id.usage', '=', 'inventory'),('product_id.id','=',product.id)] + inventory_domain)
            stock_internal_lines = self.env['stock.move'].search([('location_id.usage', '=', 'internal'),('location_dest_id.usage', '=', 'internal'),('product_id.id','=',product.id)] + inventory_domain)
            stock_internal_lines_2 = self.env['stock.move'].search([('location_id.usage', '=', 'internal'),('location_dest_id.usage', '=', 'inventory'),('product_id.id','=',product.id)] + inventory_domain)
            adjust = 0
            internal = 0
            plus_picking = 0
            if stock_pick_lines:
                for invent in stock_pick_lines:
                    adjust = invent.product_uom_qty
                    plus_picking = invent.id
            min_picking = 0
            if stock_internal_lines_2 :
                for inter in stock_internal_lines_2:
                    plus_min = inter.product_uom_qty
                    min_picking = inter.id
            if plus_picking > min_picking :
                picking_id = self.env['stock.move'].browse(plus_picking)
                adjust = picking_id.product_uom_qty
            else :
                picking_id = self.env['stock.move'].browse(min_picking)
                adjust = -int(picking_id.product_uom_qty)
            if stock_internal_lines:

                for inter in stock_internal_lines:
                    internal = inter.product_uom_qty
                    
            ending_bal = opening[product.id]['qty_available'] - sales_value + incoming + adjust
            method = ''
            price_used = product.standard_price
            if product.categ_id.property_cost_method == 'average' :
                method = 'Average Cost (AVCO)'
                price_used = avg_cost 

            elif product.categ_id.property_cost_method == 'standard' :
                method = 'Standard Price'
                price_used = product.standard_price
            
            flag = False
            for i in lines :
                if i['category'] == product.categ_id.name :
                    i['beginning'] = i['beginning'] + opening[product.id]['qty_available']
                    i['internal'] = i['internal'] + internal
                    i['incoming'] = i['incoming'] + incoming
                    i['sale_value'] = i['sale_value'] + sales_value
                    i['outgoing'] = i['outgoing'] + adjust
                    i['net_on_hand'] = i['net_on_hand'] + ending_bal
                    i['total_value'] = i['total_value'] + (ending_bal * price_used)
                    flag = True
            if flag == False :
                vals = {
                    'category': product.categ_id.name,
                    'cost_price': price_used or 0,
                    'available':  0,
                    'virtual':  0,
                    'incoming': incoming or 0,
                    'outgoing': adjust or 0,
                    'net_on_hand': ending_bal or 0,
                    'total_value': ending_bal * price_used or 0,
                    'sale_value': sales_value or 0,
                    'purchase_value':  0,
                    'beginning': opening[product.id]['qty_available'] or 0,
                    'internal':internal or 0,
                }

                lines.append(vals)
        return lines


    def print_exl_report(self):
        if xlwt:
            data  = { 'start_date': self.start_date,
             'end_date': self.end_date,'warehouse':self.warehouse,
             'category':self.category,
             'location_id':self.location_id,
             'company_id':self.company_id.name,
             'display_sum':self.display_sum,
            'currency':self.company_id.currency_id.name,
            'product_ids': self.product_ids,
            'filter_by' : self.filter_by
            }
            filename = 'Stock Valuation Report.xls'
            get_warehouse = self.get_warehouse()
            get_warehouse_name = self._get_warehouse_name()
            l1 = []
            get_company = self.get_company()
            get_currency = self.get_currency()
            workbook = xlwt.Workbook()
            stylePC = xlwt.XFStyle()
            alignment = xlwt.Alignment()
            alignment.horz = xlwt.Alignment.HORZ_CENTER
            fontP = xlwt.Font()
            fontP.bold = True
            fontP.height = 200
            stylePC.font = fontP
            stylePC.num_format_str = '@'
            stylePC.alignment = alignment
            style_title = xlwt.easyxf(
            "font:height 300; font: name Liberation Sans, bold on,color blue; align: horiz center")
            style_table_header = xlwt.easyxf("font:height 200; font: name Liberation Sans, bold on,color black; align: horiz center")
            style = xlwt.easyxf("font:height 200; font: name Liberation Sans,color black;")
            worksheet = workbook.add_sheet('Sheet 1')
            worksheet.write(5, 1, 'Start Date:', style_table_header)
            worksheet.write(6, 1, str(self.start_date))
            worksheet.write(5, 2, 'End Date', style_table_header)
            worksheet.write(6, 2, str(self.end_date))
            worksheet.write(5, 3, 'Company', style_table_header)
            worksheet.write(6, 3, get_company and get_company[0] or '',)
            worksheet.write(5, 4, 'Warehouse(s)', style_table_header)
            worksheet.write(5, 5, 'Currency', style_table_header)
            worksheet.write(6, 5, get_currency and get_currency[0] or '',)
            w_col_no = 7
            w_col_no1 = 8
            if get_warehouse_name:
                   # w_col_no = w_col_no + 8
                worksheet.write(6, 4,get_warehouse_name, stylePC)
                   # w_col_no1 = w_col_no1 + 9
            if self.display_sum:
                worksheet.write_merge(0, 1, 1, 6, "Inventory Valuation Summary Report", style=style_title)
                worksheet.write(8, 0, 'Category', style_table_header)
                worksheet.write(8, 1, 'Beginning', style_table_header)
                worksheet.write(8, 2, 'Internal', style_table_header)
                worksheet.write(8, 3, 'Received', style_table_header)
                worksheet.write(8, 4, 'Sales', style_table_header)
                worksheet.write(8, 5, 'Adjustment', style_table_header)
                worksheet.write(8, 6, 'Ending', style_table_header)
                worksheet.write(8, 7, 'Valuation', style_table_header)
                prod_row = 9
                prod_col = 0
                
                get_line = self.get_data(data)
                for each in get_line:
                    worksheet.write(prod_row, prod_col, each['category'], style)
                    worksheet.write(prod_row, prod_col+1, each['beginning'], style)
                    worksheet.write(prod_row, prod_col+2, each['internal'], style)
                    worksheet.write(prod_row, prod_col+3, each['incoming'], style)
                    worksheet.write(prod_row, prod_col+4, each['sale_value'], style)
                    worksheet.write(prod_row, prod_col+5, each['outgoing'], style)
                    worksheet.write(prod_row, prod_col+6, each['net_on_hand'], style)
                    worksheet.write(prod_row, prod_col+7, each['total_value'], style)
                    prod_row = prod_row + 1
                    
                prod_row = 8
                prod_col = 7
            else:
                worksheet.write_merge(0, 1, 2, 9, "Inventory Valuation Report", style=style_title)
                worksheet.write(8, 0, 'Default Code', style_table_header)
                worksheet.write(8, 1, 'Name', style_table_header)
                worksheet.write(8, 2, 'Category', style_table_header)
                worksheet.write(8, 3, 'Costing Method', style_table_header)
                worksheet.write(8, 4, 'Cost Price', style_table_header)
                worksheet.write(8, 5, 'Beginning', style_table_header)
                worksheet.write(8, 6, 'Internal', style_table_header)
                worksheet.write(8, 7, 'Received', style_table_header)
                worksheet.write(8, 8, 'Sales', style_table_header)
                worksheet.write(8, 9, 'Adjustment', style_table_header)
                worksheet.write(8, 10, 'Ending', style_table_header)
                worksheet.write(8, 11, 'Valuation', style_table_header)
                prod_row = 9
                prod_col = 0
                
                get_line = self.get_lines(data)
                for each in get_line:
                    worksheet.write(prod_row, prod_col, each['sku'], style)
                    worksheet.write(prod_row, prod_col+1, each['name'], style)
                    worksheet.write(prod_row, prod_col+2, each['category'], style)
                    worksheet.write(prod_row, prod_col+3, each['costing_method'], style)
                    worksheet.write(prod_row, prod_col+4, each['cost_price'], style)
                    worksheet.write(prod_row, prod_col+5, each['beginning'], style)
                    worksheet.write(prod_row, prod_col+6, each['internal'], style)
                    worksheet.write(prod_row, prod_col+7, each['incoming'], style)
                    worksheet.write(prod_row, prod_col+8, each['sale_value'], style)
                    worksheet.write(prod_row, prod_col+9, each['outgoing'], style)
                    worksheet.write(prod_row, prod_col+10, each['net_on_hand'], style)
                    worksheet.write(prod_row, prod_col+11, each['total_value'], style)
                    prod_row = prod_row + 1
                    
                prod_row = 8
                prod_col = 7
            fp = io.BytesIO()
            workbook.save(fp)
            
            export_id = self.env['sale.day.book.report.excel'].create({'excel_file': base64.encodestring(fp.getvalue()), 'file_name': filename})
            res = {
                    'view_mode': 'form',
                    'res_id': export_id.id,
                    'res_model': 'sale.day.book.report.excel',
                    'type': 'ir.actions.act_window',
                    'target':'new'
                }
            return res
        else:
            raise Warning (""" You Don't have xlwt library.\n Please install it by executing this command :  sudo pip3 install xlwt""")
        





class sale_day_book_report_excel(models.TransientModel):
    _name = "sale.day.book.report.excel"
    
    
    excel_file = fields.Binary('Excel Report For Sale Book Day ')
    file_name = fields.Char('Excel File', size=64)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
