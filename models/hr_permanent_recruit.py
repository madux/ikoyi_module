from datetime import datetime, timedelta
import time
import base64
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_is_zero, float_compare
from odoo.tools.misc import formatLang
from odoo.addons.base.res.res_partner import WARNING_MESSAGE, WARNING_HELP
import odoo.addons.decimal_precision as dp
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo import http
import re


class HR_PERMANENT_RECRUIT(models.Model):
    _name = "hr.permanent_recruit"
    _inherit = ['mail.thread', 'ir.attachment'] # 'ir.needaction_mixin']
    _description = "Human Resource HR and Offer"
    _order = "id desc"
    _rec_name = "name"

    def get_url(self, id, name):
        base_url = http.request.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        base_url += '/web# id=%d&view_type=form&model=%s' % (id, name)
        return "<a href={}> </b>Click<a/> to Review. ".format(base_url)

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)

    def _get_all_followers(self):
        followers = []
        groups = self.env['res.groups']
        hr_manager = self.env.ref('hr.group_hr_manager').id
        general_manager = self.env.ref('ikoyi_module.gm_ikoyi').id
        hod_manager = self.env.ref('ikoyi_module.ikoyi_hod').id
        hou_manager = self.env.ref('ikoyi_module.ikoyi_hou').id
        hr_user = self.env.ref('hr.group_hr_user').id

        hr_manager_group = groups.search([('id', '=', hr_manager)])
        gm_group = groups.search([('id', '=', general_manager)])
        hod_group = groups.search([('id', '=', hod_manager)])
        hou_group = groups.search([('id', '=', hou_manager)])
        hruser_group = groups.search([('id', '=', hr_user)])

        for rec in hr_manager_group:
            for users in rec.users:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', users.id)])
                for rex in employee:
                    followers.append(rex.id)

        for rec in gm_group:
            for users in rec.users:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', users.id)])
                for rex in employee:
                    followers.append(rex.id)
        for rec in hod_group:
            for users in rec.users:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', users.id)])
                for rex in employee:
                    followers.append(rex.id)

        for rec in hou_group:
            for users in rec.users:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', users.id)])
                for rex in employee:
                    followers.append(rex.id)
        for rec in hruser_group:
            for users in rec.users:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', users.id)])
                for rex in employee:
                    followers.append(rex.id)

        return followers

    READONLY_STATES = {
        'HR Officer1': [('readonly', True)],
        'HR manager1': [('readonly', True)],
        'HR manager2': [('readonly', True)],

    }

    REQUIRED_STATES = {
        'HR Officer1': [('required', True)],
    }

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('hr.permanent_recruit')
        vals['name'] = str(sequence)
        return super(HR_PERMANENT_RECRUIT, self).create(vals)

    name = fields.Char(
        'Description Reference',
        required=False,
        readonly=False,
        index=True,
        copy=False,
        default='-')
    candidate_email = fields.Char(
        'Candidate\'s Email',
        required=True,
        readonly=False)
    candidate_name = fields.Char(
        'Candidate\'s Name',
        required=True,
        readonly=False)
     
    phone = fields.Char('Phone')
    user_id = fields.Many2one(
        'res.users',
        string="Users", readonly=True,
        default=lambda a: a.env.user.id)
    department_id = fields.Many2one(
        'hr.department',
        string="Proposed Department",
        required=True, states=REQUIRED_STATES)
 
    date_order = fields.Datetime(
        'Date',
        required=True,
        states=READONLY_STATES,
        index=True,
        copy=False,
        default=fields.Datetime.now)
    # ********************
    date_resumption = fields.Date( 
        'ResumptionDate',
        required=False)
    
    users_followers = fields.Many2many(
        'hr.employee',
        string='Add followers',
        required=False,
        default=_get_all_followers)

    file_upload_resumes_letter = fields.Binary('Upload Resumes') # HR HR Assistant'
    binary_fname = fields.Char('Binary Name')
    
    file_upload_acceptance = fields.Binary('Upload Acceptance Letter') # HR Officer1
    binaryaccept_fname = fields.Char('Binary Name')

    file_upload_reject = fields.Binary('Upload Rejection Letter') # HR Officer1
    binaryreject_fname = fields.Char('Binary Name')

    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        index=True,
        states=READONLY_STATES,
        default=lambda self: self.env.user.company_id.id)

    employee_id = fields.Many2one(
        'hr.employee', states=READONLY_STATES,
        string='Employee',
        required=True,
        default=_default_employee)

    notes = fields.Text('Terms and Conditions')

    description_two = fields.Text('Refusal Reasons')
    state = fields.Selection([('HR Officer1', 'Initiate'),
                              ('HR manager1', 'HR Manager'),
                              ('HR manager2', 'HR Manager'),
                              ('Executive', 'Executive'),
                              ('HR Officer2', 'HR Officer'),
                              ('HR Assistant', 'HR Assistant'),
                              ('Rejected', 'Rejected'),
                              ('Accepted', 'Accepted'),
                              ('Complete', 'Complete')],
                             string='Status', readonly=True, index=True,
                             copy=False, default='HR Officer1',
                             track_visibility='onchange')
    emp_type = fields.Selection([('Senior', 'Senior Management'),
                                ('Junior', 'Junior')], 
                                string='Type', readonly=True, index=True,
                                copy=True, default='Junior',
                                track_visibility='onchange')
    status = fields.Selection([('Successful', 'Employed'),
                                ('Dropped', 'Dropped'),
                                ('Terminated', 'Successful'),
                                ('Suspended', 'Suspended')], 
                                string='Status', readonly=False, index=True,
                                copy=True,
                                track_visibility='onchange')
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='No. Attachments')

    # ##################################################### 
    
    @api.multi
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'hr.permanent_recruit'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for rec in self:
            rec.attachment_number = attachment.get(rec.id, 0)
    @api.multi
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'hr.permanent_recruit'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'hr.permanent_recruit', 'default_res_id': self.id}
        return res

    # @api.multi
    # def button_rejects(self):
    #     if not self.description_two:
    #         raise ValidationError(
    #             'Please Add a Remark in the Refusal Note tab below')
    #     else:
    #         if self.state == "HR Assistant":
    #             self.state = "HR Officer1"
    #             self.reject_mail_hr_Assistant()
    #         elif self.state == "HR manager1":
    #             self.state = "HR Assistant"
    #             self.reject_mail_hrmanager()
    #         elif self.state == "GM":
    #             self.state = "HR manager1"
    #             self.reject_mail_gm()
            
    @api.one
    def hr_officer_approve(self):#  HR Officer
        self.write({'state': 'HR manager1', 'description_two':''})
        bodyx = "Dear Sir, <br/>This is to inform you that lists of potential candidates have been initiated\
        to you for review.  <br/>\
        Kindly {} <br/>\
        Regards".format(self.get_url(self.id, self._name))
        body = bodyx    
        return self.send_mail_mesage(body)
    
    @api.one
    def hr_manager_approve(self):#  HR manager 1
        self.write({'state': 'HR Assistant', 'description_two':''})
        bodyx = "Dear Sir, <br/>This is to inform you that lists of potential candidates have been initiated\
        to you for review.  <br/>\
        Kindly {} <br/>\
        Regards".format(self.get_url(self.id, self._name))
        body = bodyx    
        return self.send_mail_mesage(body)
    
    @api.one
    def hr_assistant_approve(self):#  HR Assistant
        self.write({'state': 'Executive', 'description_two':''})
        bodyx = "Dear Sir, <br/>This is to inform you that lists of potential candidates have been initiated\
        to you for review.  <br/>\
        Kindly {} <br/>\
        Regards".format(self.get_url(self.id, self._name))
        body = bodyx    
        return self.send_mail_mesage(body)
    
    @api.one
    def executive_approve(self):#  Executive
        self.write({'state': 'HR manager2', 'description_two':''})
        bodyx = "Dear Sir, <br/>This is to inform you that the lists of potential candidates have been approved by the executive management. <br/>\
        Kindly {} <br/>\
        Regards".format(self.get_url(self.id, self._name))
        body = bodyx    
        return self.send_mail_mesage(body)
  
    @api.one
    def hr_manager2_approve(self):#  HR manager 1
        self.write({'state': 'HR Officer2', 'description_two': ''})
        bodyx = "Dear Sir, <br/>This is to inform you that candidates in the successful status have passed all levels of approval\
        You <br/>\
        Kindly {} <br/>\
        Regards".format(self.get_url(self.id, self._name))
        body = bodyx    
        return self.send_mail_mesage(body)

    @api.multi
    def create_employee(self): 
        view = self.env.ref('hr.view_employee_form')
        return {
            'name': "Employee Creation",
            'view_type': 'form',
            "view_mode": 'form',
            'res_model': 'hr.employee',
            'type': 'ir.actions.act_window',
            'view_id': view.id,
            'target': 'current',
            'context': {
                'default_name': self.candidate_name,
                'default_work_email': self.candidate_email,
                'default_department_id': self.department_id.id,
                'default_mobile_phone': self.phone 
            },
        }

    def send_mail_mesage(self, body):
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.ikoyi_hod').id
        group_user_id = self.env.ref('hr.group_hr_manager').id
        group_user_id3 = self.env.ref('hr.group_hr_user').id

        if self.id:
            bodyx = body
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx) 
        else:
            raise ValidationError('No Record created')
        
    def mail_sending_for_three(
            self,
            email_from,
            group_user_id,
            group_user_id2,
            group_user_id3,
            bodyx):
        from_browse = self.env.user.name
        groups = self.env['res.groups']
        for order in self:
            group_users = groups.search([('id', '=', group_user_id)])
            group_users2 = groups.search([('id', '=', group_user_id2)])
            group_users3 = groups.search([('id', '=', group_user_id3)])
            group_emails = group_users.users
            group_emails2 = group_users2.users
            group_emails3 = group_users3.users

            append_mails = []
            append_mails_to = []
            append_mails_to3 = []
            for group_mail in group_emails:
                append_mails.append(group_mail.login)

            for group_mail2 in group_emails2:
                append_mails_to.append(group_mail2.login)

            for group_mail3 in group_emails3:
                append_mails_to3.append(group_mail3.login)

            all_mails = append_mails + append_mails_to + append_mails_to3
            # print all_mails
            email_froms = str(from_browse) + " <" + str(email_from) + ">"
            mail_sender = (', '.join(str(item) for item in all_mails))
            subject = "HR Notification"
            
            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': mail_sender,
                #'email_cc': mail_sender,
                'reply_to': email_from,
                'body_html': bodyx
            }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)
  