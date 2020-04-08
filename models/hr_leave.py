#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Vasconsolutions
#
# Created:     04/09/2018
# Copyright:   (c) Vasconsolutions 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import time
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError
from odoo.tools import misc, DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta
import datetime
from odoo import fields, models, api, _
from odoo.exceptions import UserError, except_orm, AccessError, ValidationError

from datetime import datetime, timedelta


class HolidaysType(models.Model):
    _inherit = "hr.holidays.status"
    
    is_annual = fields.Selection([
        ('annual', 'Annual Leave'),
        ('compensate', 'Compensatory'),
        ('maternity', 'Maternity'),
        ('Paternity', 'Paternity'),
        ('death', 'Death'),
        ('sick', 'Sick'),
        ('validate', 'Approved')
        ], string='Category ', readonly=False, track_visibility='onchange', copy=False, )

    double_validation = fields.Boolean(string='Apply Double Validation', default=True,
        help="When selected, the Allocation/Leave Requests for this type require a second validation to be approved.")
    
HOURS_PER_DAY = 8
  
  
class Holidays(models.Model):
    _inherit = 'hr.holidays'

    instant_bonus = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'), 
        ], string='Pay Bonus ?', default="no",
                                     readonly=False,
                                     track_visibility='onchange',
                                     copy=False, )
    
    is_senior_manager = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No'), 
        ], string='Is Senior Staff ?', default="no", readonly=False,
                                         track_visibility='onchange', copy=False, )
 
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('unit_manager', 'Unit Manager'), 
        ('hod', 'HOD'), 
        ('confirm', 'HR To Approve'), # hr
        ('validate1', 'GM To Approve'), # gm manager
        ('validate', 'Approved'), # gm
        ('refuse', 'Refused'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, track_visibility='onchange', copy=False, default='draft',
            help="The status is set to 'To Submit', when a holiday request is created." +
            "\nThe status is 'To Approve', when holiday request is confirmed by user." +
            "\nThe status is 'Refused', when holiday request is refused by manager." +
            "\nThe status is 'Approved', when holiday request is approved by manager.")
    
    @api.multi
    def action_confirm(self):
        if self.filtered(lambda holiday: holiday.state != 'draft'):
            raise UserError(_('Leave request must be in Draft state ("To Submit") in order to confirm it.'))
        return self.write({'state': 'unit_manager'})
    
    @api.multi
    def action_unit_confirm(self):
        return self.write({'state': 'hod'})
    
    @api.multi
    def action_hod_confirm(self):
        return self.write({'state': 'confirm'})
    
    @api.multi
    def action_validate(self):
        if not self.env.user.has_group('ikoyi_module.gm_ikoyi'):
            raise UserError(_('Only GM can validate a leave requests.'))

        manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        for holiday in self:
            if holiday.state not in ['confirm', 'validate1']:
                raise UserError(_('Leave request must be confirmed in order to approve it.'))
            if holiday.state == 'validate1' and not holiday.env.user.has_group('hr_holidays.group_hr_holidays_manager'):
                raise UserError(_('Only an HR Manager can apply the second approval on leave requests.'))

            holiday.write({'state': 'validate'})
            if holiday.double_validation:
                holiday.write({'manager_id2': manager.id})
            else:
                holiday.write({'manager_id': manager.id})
            if holiday.holiday_type == 'employee' and holiday.type == 'remove':
                meeting_values = {
                    'name': holiday.display_name,
                    'categ_ids': [(6, 0, [holiday.holiday_status_id.categ_id.id])] if holiday.holiday_status_id.categ_id else [],
                    'duration': holiday.number_of_days_temp * HOURS_PER_DAY,
                    'description': holiday.notes,
                    'user_id': holiday.user_id.id,
                    'start': holiday.date_from,
                    'stop': holiday.date_to,
                    'allday': False,
                    'state': 'open',            # to block that meeting date in the calendar
                    'privacy': 'confidential'
                }
                #Add the partner_id (if exist) as an attendee
                if holiday.user_id and holiday.user_id.partner_id:
                    meeting_values['partner_ids'] = [(4, holiday.user_id.partner_id.id)]

                meeting = self.env['calendar.event'].with_context(no_mail_to_attendees=True).create(meeting_values)
                holiday._create_resource_leave()
                holiday.write({'meeting_id': meeting.id})
            elif holiday.holiday_type == 'category':
                leaves = self.env['hr.holidays']
                for employee in holiday.category_id.employee_ids:
                    values = holiday._prepare_create_by_category(employee)
                    leaves += self.with_context(mail_notify_force_send=False).create(values)
                # TODO is it necessary to interleave the calls?
                leaves.action_approve()
                if leaves and leaves[0].double_validation:
                    leaves.action_validate()
        return True
     