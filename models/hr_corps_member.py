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


class HR_CORPS(models.Model):
    _name = "hr.corps"
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
        sequence = self.env['ir.sequence'].next_by_code('hr.corps')
        vals['name'] = str(sequence)
        return super(HR_CORPS, self).create(vals)

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
    sec_phone = fields.Char('Phone')  # **********************
    sec_email = fields.Char(
        'Secretariat\'s Email',
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
                              ('HR Officer2', 'HR Officer'),
                              ('HR Officer3', 'HR Officer'),
                              ('HR Officer4', 'HR Officer'),
                              ('HR manager1', 'HR Manager'),
                              ('HR manager2', 'HR Manager'),
                              ('GM1', 'GM'),
                              ('GM2', 'GM 2nd Approval'),
                              ('Waiting', 'Waiting'),
                              ('Rejected', 'Rejected'),
                              ('Accepted', 'Accepted'),
                              ('Complete', 'Complete')],
                             string='Status', readonly=True, index=True,
                             copy=False, default='HR Officer1',
                             track_visibility='onchange')
    emp_type = fields.Selection([('Intern', 'Intern'),
                              ('Consultant', 'Consultant'),
                              ('Contractor', 'Contractor'),
                              ('Full Term', 'Full Term'),
                              ('Part Time', 'Part Time'),
                              ('NYSC', 'NYSC')],
                            string='Type', readonly=True, index=True,
                            copy=True, default='NYSC',
                            track_visibility='onchange')
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='No. Attachments')

    # ##################################################### 
    
    @api.multi
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'hr.corps'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for rec in self:
            rec.attachment_number = attachment.get(rec.id, 0)
    @api.multi
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'hr.corps'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'hr.corps', 'default_res_id': self.id}
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
    def hr_assistant_approve(self):#  HR Officer
        self.write({'state': 'HR manager1', 'description_two':''})
        bodyx = "Dear Sir, <br/>This is to inform you that a request for NYSC corps recruitment have been initiated\
        to you for review and approval. <br/>\
        Kindly {} <br/>\
        Regards".format(self.get_url(self.id, self._name))
        filename = self.file_upload_acceptance 
        body = bodyx  
        attachment_name = str(self.candidate_name) + " Resume"        
        return self.send_mail2(filename, body, attachment_name)
    
    @api.one
    def hr_manager_approve(self):#  HR manager 1
        self.write({'state': 'GM1', 'description_two':''})
        bodyx = "Dear Sir, <br/>This is to inform you that a request for NYSC corps recruitment have been initiated\
        to you for review and approval. <br/>\
        Kindly {} <br/>\
        Regards".format(self.get_url(self.id, self._name))
        filename = self.file_upload_acceptance 
        body = bodyx    
        attachment_name = str(self.candidate_name) + " Acceptance Letter"        
        return self.send_mail2(filename, body, attachment_name)
    
    @api.one
    def gm_approve(self):#  GM
        self.write({'state': 'HR Officer2', 'description_two':''})
        bodyx = "Dear Sir, <br/>This is to inform you that a request for NYSC corps recruitment have been initiated\
        to you for review and approval. <br/>\
        Kindly {} <br/>\
        Regards".format(self.get_url(self.id, self._name))
        filename = self.file_upload_acceptance 
        body = bodyx    
        attachment_name = str(self.candidate_name) + " Resume(GM Upload)"        
        return self.send_mail2(filename, body, attachment_name)
    
    @api.one
    def hrofficer_to_candidate(self):
        self.write({'state': 'Accepted', 'description_two': ''})
        return self.send_mail5()

    def send_mail5(self, force=False):
        email_from = self.env.user.company_id.email
        mail_to = self.candidate_email
        bodyx = "Dear, <br/>This is to inform you that you that your Offer to serve in our organization as a corp member \
        have been accepted. Your date of resumption is {} <br/> \
        Kindly contact Ikoyi Club 1938 - Department: ({}), to indicate your interest. \
        Regards".format(self.date_resumption, self.department_id.name)

        self.mail_sending_candidate(email_from, mail_to, bodyx)

    def mail_sending_candidate(self, email_from, mail_to, bodyx):
        subject = "EMPLOYEMENT LETTER"
        mail_data = {
                'email_from': email_from,
                'subject': subject,
                'email_to': mail_to,
                'reply_to': email_from,
                'body_html': bodyx
            }
        mail_id = self.env['mail.mail'].create(mail_data)
        self.env['mail.mail'].send(mail_id)

    @api.multi
    def send_mail2(self, filename, body, attachment_name, force=False):
        email_from = self.env.user.company_id.email
        group_user_id = self.env.ref('hr.group_hr_manager').id
        subject = "NYSC Corps Recruitment Notification"
        bodyx = body
        filename = filename
        attachment_name = attachment_name
        self.mail_sending_attachment(email_from, group_user_id, bodyx, 
                                     subject, filename, attachment_name)

    def mail_sending_attachment(self, email_from, group_user_id, bodyx, 
                                subject, filename, attachment_name):
        lists = []
        # save pdf as attachment 
        ATTACHMENT_NAME = attachment_name
        tech = self.env['ir.attachment'].create({
            'name': ATTACHMENT_NAME,
            'type': 'binary',
            'datas': filename,
            'datas_fname': filename, #ATTACHMENT_NAME + '.pdf',
            'store_fname': ATTACHMENT_NAME,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/x-pdf'
        })
        lists.append(tech.id)

        groups = self.env['res.groups']
        for order in self:
            group_users = groups.search([('id', '=', group_user_id)])
            group_emails = group_users.users
            followers = []
            email_to = []
            for group_mail in self.users_followers:
                followers.append(group_mail.work_email)

            for gec in group_emails:
                email_to.append(gec.login)
            followers_appends = (', '.join(str(item) for item in followers))
            mail_tos = (','.join(str(item2) for item2 in email_to))
            email_froms = "Ikoyi Club " + " <" + str(email_from) + ">"
            subject = subject
            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': mail_tos,
                'reply_to': email_from,
                'email_cc': followers_appends,
                'attachment_ids': [(6, 0, lists)] or None,
                'body_html': bodyx,
                        }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)
    
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
        
    @api.one
    def set_hr_manager_reject(self):  # HR OFFICER SEES IT
        if not self.file_upload_reject:
            raise ValidationError('please Upload the rejection outcome note')
        else:
            self.write({'state': 'HR manager2', 'description_two': ''}) 
            body = "Dear Sir, <br/>This is to inform all HODs / Admins\
            that the request to recruit {} for NYSC service has been rejected by the organization \
            Kindly {} to view the outcome of the rejection. <br/>\
            Regards".format(self.candidate_name, self.get_url(self.id, self._name))
            filename = self.file_upload_reject
            attachment_name = str(self.candidate_name) + " Rejection Note"        
            return self.send_mail2(filename, body, attachment_name)
        
    @api.one
    def set_hrm_gm_reject(self):
        if not self.file_upload_reject:
            raise ValidationError('please Upload the rejection outcome note')
        else:
            self.write({'state': 'GM2', 'description_two': ''}) 
            body = "Dear Sir, <br/>This is to inform all HODs / Admins\
            that the request to recruit with Reference {} has been rejected by the organization \
            Kindly {} to view the outcome of the rejection. <br/>\
            Regards".format(self.name, self.get_url(self.id, self._name))
            filename = self.file_upload_reject 
            attachment_name = str(self.candidate_name) + " Rejection Outcome Note"        
            return self.send_mail2(filename, body, attachment_name)
       
        
    @api.one
    def GM_rejection(self):  # HR OFFICER SEES IT
        self.write({'state': 'Rejected', 'description_two': ''})
        return self.send_mail6()

    def send_mail6(self, force=False):
        email_from = self.env.user.company_id.email
        mail_to = self.sec_email
        bodyx = "Hello, <br/>This is to inform that you that your Offer to post {} in our organization as a corp member \
        have been rejected. Kindly contact Ikoyi Club 1938 - Department: ({}), for any enquiry. \
        Regards".format(self.employee_id.name, self.department_id.name)

        self.mail_sending_candidate(email_from, mail_to, bodyx)
        
    #
    # ############################################################
    