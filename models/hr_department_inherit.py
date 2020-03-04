from datetime import datetime, timedelta
import time
from dateutil.relativedelta import relativedelta

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError

# MOF REQUEST WORKFLOW --


class Inherit_employee(models.Model):
    _inherit = "hr.employee"

    unit_emp = fields.Many2one('hr.unit', 'Unit', required=False)
    unit_manager = fields.Many2one('hr.employee', 'Unit Manager')
    # , related='unit_manager.user_id.id')
    unit_user = fields.Many2one('res.users', string='Related Unit User')
    
    @api.onchange('unit_emp')
    def get_manager(self):
        for rec in self:
            if rec.unit_emp:
                rec.unit_manager = rec.unit_emp.manager.id
                rec.unit_user = rec.unit_emp.manager.user_id.id
                rec.department_id = rec.unit_emp.department.id


class Unit_department(models.Model):
    _name = "hr.unit"
    name = fields.Char('Unit Name')
    department = fields.Many2one('hr.department', 'Department')
    manager = fields.Many2one('hr.employee', 'Manager')
    user = fields.Many2one('res.users', compute="get_manager")
    @api.depends('department')
    def get_manager(self):
        for rec in self:
            if rec.department:
                rec.manager = rec.department.manager_id.id
                rec.user = rec.department.manager_id.user_id.id


class Hr_Department(models.Model):
    _inherit = "hr.department"

    account_recievable = fields.Many2one(
        'account.account', 'Account Receivable', required=True)
    account_payable = fields.Many2one(
        'account.account',
        'Account Payabale',
        required=True)

    department_email = fields.Char('Department Email')
