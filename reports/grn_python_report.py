# -*- coding: utf-8 -*-

import time
from odoo import api, models
from dateutil.parser import parse
from odoo.exceptions import ValidationError


class ReportGRN(models.AbstractModel):
    _name = 'report.ikoyi_module.report_grn'
    
    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        sales_records = []
        orders = self.env['stock.picking'].search([('id', '=', docs.stock_id.id)])
        for order in orders:
            sales_records.append(order);
        else:
            raise ValidationError("No record found")
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'time': time,
            'orders': sales_records
        }
        return self.env['report'].render('ikoyi_module.print_grn_view_template', docargs)
