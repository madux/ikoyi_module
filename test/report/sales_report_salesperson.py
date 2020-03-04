# -*- coding: utf-8 -*-

import time
from odoo import api, models
from dateutil.parser import parse
from odoo.exceptions import UserError


class ReportSalesperson(models.AbstractModel):
    _name = 'report.sales_report.report_salesperson'
    
    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        sales_records = []
        orders = self.env['sale.order'].search([('user_id', '=', docs.salesperson_id.id)])
        if docs.date_from and docs.date_to:
            for order in orders:
                if parse(docs.date_from) <= parse(order.date_order) and parse(docs.date_to) >= parse(order.date_order):
                    sales_records.append(order);
        else:
            raise UserError("Please enter duration")
        
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'time': time,
            'orders': sales_records
        }
        return self.env['report'].render('sales_report.report_salesperson', docargs)
