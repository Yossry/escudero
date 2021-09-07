# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.


from odoo import models, api
from datetime import date
from odoo.tools.float_utils import float_round


class sales_daybook_product_category_report(models.AbstractModel):
    _name = 'report.bi_inventory_valuation_reports.sales_daybook_template'
    
    def _get_report_values(self, docids, data=None):
        data = data if data is not None else {}
        docs = self.env['sale.day.book.wizard'].browse(docids)
        data  = {'product_ids':docs.product_ids , 'filter_by':docs.filter_by,'start_date': docs.start_date, 'end_date': docs.end_date,'warehouse':docs.warehouse,'category':docs.category,'location_id':docs.location_id,'company_id':docs.company_id.name,'display_sum':docs.display_sum,'currency':docs.company_id.currency_id.name}
        return {
                   'doc_model': 'sale.day.book.wizard',
                   'data' : data,
                   'get_warehouse' : self._get_warehouse_name,
                   'get_lines':self._get_lines,
                   'get_data' : self._get_data,
                   }

    def _get_warehouse_name(self,data):
        if data:
            l1 = []
            l2 = []
            for i in data:
                l1.append(i.name)
                myString = ",".join(l1 )
            return myString
        return ''
    
    def _get_company(self, data):
        if data['company_id']:
            l1 = []
            l2 = []
            obj = self.env['res.company'].search([('name', '=', data['company_id'])])
            l1.append(obj.name)
            return l1
        return ''

    def _get_currency(self,data):
        if data['company_id']:
            l1 = []
            l2 = []
            obj = self.env['res.company'].search([('name', '=', data['company_id'])])
            l1.append(obj.currency_id.name)
            return l1
        return ''
    



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
        # only to_date as to_date will correspond to qty_available
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
    
    

    def _get_lines(self, data):
            product_res = self.env['product.product'].search([('qty_available', '!=', 0),
                                                                ('type', '=', 'product'),

                                                                ])
            category_lst = []
            if data['category']  and data['filter_by'] == 'categ':
                for cate in data['category'] :
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

                stock_move_line = self.env['stock.move'].search([
                    ('product_id','=',product.id),
                    ('date','>',data['start_date']),
                    ('date',"<=",data['end_date']),
                    ('state','=','done')
                    ] + custom_domain)

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
############################### MODIFY create_date por force_date #################################
                stock_val_layer = self.env['stock.valuation.layer'].search([
                        ('product_id','=',product.id),
                        ('force_date','>=',data['start_date']),
                        ('force_date',"<=",data['end_date']),
                        
                        ] )

                cost = 0
                qty = 0
                for layer in stock_val_layer :
                        if layer.stock_move_id.picking_id.picking_type_id.code == "incoming" :
                            cost = cost + layer.value
                            qty = qty + layer.quantity

                        if not layer.stock_move_id.picking_id :
                            cost = cost + layer.value
                            qty = qty + layer.quantity

                avg_cost = 0
                if qty > 0 :
                    avg_cost = cost / qty
                    avg_cost = round(avg_cost, 2)

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



    def _get_data(self,data):
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
                print ("obj----------comp----------------------",obj.name)
                custom_domain.append(('company_id','=',obj.id))
            if data['warehouse'] :
                warehouse_lst = [a.id for a in data['warehouse']]
                custom_domain.append(('picking_id.picking_type_id.warehouse_id','in',warehouse_lst))
            stock_move_line = self.env['stock.move'].search([
                ('product_id','=',product.id),
                ('date','>',data['start_date']),
                ('date',"<=",data['end_date']),
                ('state','=','done')
                ] + custom_domain)
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
       
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
