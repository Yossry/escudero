# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from openerp.exceptions import Warning
from datetime import datetime
import pytz
import json
from odoo.tools import date_utils
from odoo.addons.hyd_stock_card.reports.stock_card_report import get_values
from odoo.addons.hyd_stock_card.reports.stock_card_details_report import get_values as get_values_d


FORMAT_DATE = "%Y-%m-%d"
ERREUR_FUSEAU = _("Set your timezone in preferences")


class StockCardWizard(models.TransientModel):
    u"""."""

    _name = "wizard.stock_card_wizard"

    details = fields.Boolean(
        string="Detailed report",
        default=True)

    date_start = fields.Date(
        string="Fecha Inicial",
        required=True)

    date_end = fields.Date(
        string="Fecha Final",
        required=True)

    location_id = fields.Many2one(
        string="Ubicación",
        comodel_name="stock.location",
        domain=[('usage','=','internal')],
        required=True)

    group_by_category = fields.Boolean(
        string="Group by category",
        default=True)

    group_by_serial = fields.Boolean(
        string="Agrupar por Lote",
        default=False)

    filter_by = fields.Selection(
        string="Filtrar por",
        required=True,
        selection=[
            ('no_filter', 'Sin Filtro'),
            ('product', 'Producto'),
            ('category', 'Categoría')],
        default='no_filter')

    products = fields.Many2many(
        string="Productos",
        comodel_name="product.product",
        domain=[('type','=','product')])

    category = fields.Many2one(
        string="Categoría",
        comodel_name="product.category",
        help="Select category to filter")

    is_zero = fields.Boolean(
        string='Sin Mov',
        default=False,
        help="""Unselect if you just want to see product who have move"""
             """ in the period.""")
    show_cost = fields.Boolean(
        string="Mostrar Costo",
        default=True)

    @api.model
    def convert_UTC_TZ(self, UTC_datetime):
        if not self.env.user.tz:
            raise Warning(ERREUR_FUSEAU)
        local_tz = pytz.timezone(self.env.user.tz)
        date = datetime.strptime(str(UTC_datetime), FORMAT_DATE)
        date = pytz.utc.localize(date, is_dst=None).astimezone(local_tz)
        return date.strftime(FORMAT_DATE)

    def print_card(self):
        """Print the stock card."""
        self.ensure_one()

        location = self.location_id
        warehouse = None
        warehouses = self.env['stock.warehouse'].search([])
        for war in warehouses:
            wlocation = war.view_location_id
            if location.parent_path.startswith(wlocation.parent_path):
                warehouse = war
                break

        context = self.env.context
        is_excel = context.get("xls_export", False)

        datas = {}
        datas['date_start'] = self.convert_UTC_TZ(self.date_start)
        datas['date_end'] = self.convert_UTC_TZ(self.date_end)
        datas['start'] = self.date_start
        datas['end'] = self.date_end
        datas['location_id'] = location.id
        datas['group_by_serial'] = self.group_by_serial
        datas['group_by_category'] = self.group_by_category
        datas['filter_by'] = self.filter_by
        datas['category_id'] = self.category.id if self.category else None
        datas['category_name'] = self.category.name if self.category else None
        datas['products'] = self.products.mapped('id')
        datas['products_name'] = ','.join(self.products.mapped('name'))
        datas['location_name'] = location.name
        datas['warehouse_name'] = warehouse.name
        datas['details'] = self.details
        datas['is_zero'] = self.is_zero
        datas['show_cost'] = self.show_cost

        report_name = 'hyd_stock_card.stock_card_report'
        if self.group_by_serial or self.show_cost:
            report_name = 'hyd_stock_card.stock_card_report_landscape'
        report_excel = 'hyd_stock_card.stock_card_xlsx'
        get_exl_vals = get_values
        if self.details:
            report_name = 'hyd_stock_card.stock_card_details_report'
            report_excel = 'hyd_stock_card.stock_card_details_xlsx'
            get_exl_vals = get_values_d

        if is_excel:
            return self.env.ref(
                report_excel).report_action(
                self, data=get_exl_vals(self, datas))
        else:
            return self.env.ref(report_name).report_action(self, data=datas)


    