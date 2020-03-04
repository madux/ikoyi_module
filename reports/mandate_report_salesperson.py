# -*- coding: utf-8 -*-

import time
from odoo import api, models
from dateutil.parser import parse
from odoo.exceptions import ValidationError


class ReportSalespersonMandate(models.AbstractModel):
    _name = 'report.ikoyi_module.report_mandate'
    
    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        sales_records = []
        orders = self.env['payment.mandate.ikoyi'].search([('vendor_bank','in', docs.vendor_bank.ids),('create_uid', '=', docs.salesperson_id.id)])
        if docs.date_from and docs.date_to:
            for order in orders:
                if parse(docs.date_from) <= parse(order.date_sche) and parse(docs.date_to) >= parse(order.date_sche):
                    sales_records.append(order);
        else:
            raise ValidationError("Please enter duration")
        
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'time': time,
            'orders': sales_records
        }
        return self.env['report'].render('ikoyi_module.report_mandate', docargs)
