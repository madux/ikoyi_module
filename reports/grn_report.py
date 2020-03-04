# -*- coding: utf-8 -*-

import time
from odoo import api, models
from dateutil.parser import parse
from odoo.exceptions import UserError

class ReportGRN(models.AbstractModel):
    _name = 'report.ikoyi_module.report_grnx'

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(self.env.context.get('active_id'))
        lists = []
        orders = self.env['stock.picking'].search([('id', '=', docs.stock_id.id)])
        if docs.stock_id:
            for order in orders:
                lists.append(order)
        else:
            raise UserError("No Stock")
        docargs = {
            'doc_ids': self.ids,
            'doc_model': self.model,
            'docs': docs,
            'time': time, 
            'orders': lists
        }
        return self.env['report'].render('ikoyi_module.report_grnx', docargs)
