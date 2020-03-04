# -*- coding: utf-8 -*-

from odoo import api, fields, models


class MandateWizard(models.TransientModel):
    _name = "mandate.wizardho"
    _description = "Salesperson wizard"
    
    salesperson_id = fields.Many2one('res.users', string='User', required=True, default=lambda self: self.env.uid)
    date_from = fields.Datetime(string='Start Date')
    date_to = fields.Datetime(string='End Date')
    vendor_bank = fields.Many2many(
        'res.bank',
        string='Vendor Bank',
        readonly=False)

    @api.multi
    def check_report(self):
        data = {}
        data['form'] = self.read(['salesperson_id', 'date_from', 'date_to', 'vendor_bank'])[0]
        return self._print_report(data)

    def _print_report(self, data):
        data['form'].update(self.read(['salesperson_id', 'date_from', 'date_to','vendor_bank'])[0])
        return self.env['report'].get_action(self, 'ikoyi_module.report_mandate', data=data)
