# -*- coding: utf-8 -*-

from odoo import api, fields, models


class GRNWizard(models.TransientModel):
    _name = "grn.wizardho"
    _description = "Goods Requisition wizard"
    
    stock_id = fields.Many2one('stock.picking', string='Stock Reference', required=True)

    @api.multi
    def check_report(self):
        data = {}
        data['form'] = self.read(['stock_id'])[0]
        return self._print_report(data)

    def _print_report(self, data):
        data['form'] = self.read(['stock_id'])[0]
        data['form'].update(self.read(['stock_id'])[0])
        return self.env['report'].get_action(self, 'ikoyi_module.report_grnx', data=data)
