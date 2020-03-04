# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SalespersonWizard(models.TransientModel):
    _name = "salesperson.wizard"
    _description = "Salesperson wizard"
    
    salesperson_id = fields.Many2one('res.users', string='Salesperson', required=True)
    date_from = fields.Datetime(string='Start Date')
    date_to = fields.Datetime(string='End Date')

    @api.multi
    def check_report(self):
        data = {}
        data['form'] = self.read(['salesperson_id', 'date_from', 'date_to'])[0]
        return self._print_report(data)

    def _print_report(self, data):
        data['form'].update(self.read(['salesperson_id', 'date_from', 'date_to'])[0])
        return self.env['report'].get_action(self, 'sales_report.report_salesperson', data=data)