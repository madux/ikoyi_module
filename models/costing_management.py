
from datetime import datetime, timedelta
import time
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError

"""Docs: Open costing menu (Stock Quantity = (open the Product Quantities))
2. Create A wizard report for stock quant: """


class Cost_Management(models.Model):
    _name = "cost.management"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "Cost Management"
    _order = "id desc"

    user_id = fields.Many2one('res.users', string='User', required=False)
    name = fields.Char('Description')
    
class CostingWizard(models.TransientModel):
    _name = "costing.wizard"
    _description = "Costing wizard"
    
    salesperson_id = fields.Many2one('res.users', string='Salesperson', required=False)
    date_from = fields.Datetime(string='Start Date')
    date_to = fields.Datetime(string='End Date')
    location_ids = fields.Many2many(
        'stock.location',
        string='Stores / Location',
        readonly=False, required=True)

    @api.multi
    def check_report(self):
        data = {}
        data['form'] = self.read(['date_from', 'date_to', 'location_ids'])[0]
        return self._print_report(data)

    def _print_report(self, data):
        data['form'].update(self.read(['date_from', 'date_to','location_ids'])[0])
        return self.env['report'].get_action(self, 'ikoyi_module.report_stock', data=data) # the template ID is existing in /views/costing_report_wizard.xml


class ReportStocks(models.AbstractModel):
    _name = 'report.ikoyi_module.report_stock'

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        stock_records = []
        orders = self.env['stock.quant'].search([('location_id','in', docs.location_ids.ids)])
        if docs.date_from and docs.date_to:
            for order in orders:
                if parse(docs.date_from) <= parse(order.in_date) and parse(docs.date_to) >= parse(order.in_date):
                    stock_records.append(order);
        else:
            raise UserError("Please enter duration")
        
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'time': time,
            'orders': stock_records
        }
        return self.env['report'].render('ikoyi_module.report_stock', docargs)
