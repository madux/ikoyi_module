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


class HR_OFFER_MANAGEMENT(models.Model):
    _name = "hr.offer.management"
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
        # chairman = self.env.ref('ikoyi_module.chairman_ikoyi').id
        # vice_chairman = self.env.ref('ikoyi_module.vice_chairman_ikoyi').id
        general_manager = self.env.ref('ikoyi_module.gm_ikoyi').id
        hod_manager = self.env.ref('ikoyi_module.ikoyi_hod').id
        hou_manager = self.env.ref('ikoyi_module.ikoyi_hou').id
        hr_user = self.env.ref('hr.group_hr_user').id

        hr_manager_group = groups.search([('id', '=', hr_manager)])
        # chairman_group = groups.search([('id', '=', chairman)])
        # vc_group = groups.search([('id', '=', vice_chairman)])
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

        '''for rec in chairman_group:
            for users in rec.users:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', users.id)])
                for rex in employee:
                    followers.append(rex.id)

        for rec in vc_group:
            for users in rec.users:
                employee = self.env['hr.employee'].search(
                    [('user_id', '=', users.id)])
                for rex in employee:
                    followers.append(rex.id)'''

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
        'HR Officer2': [('required', True)],
    }

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('hr.offer.management')
        vals['name'] = str(sequence)
        return super(HR_OFFER_MANAGEMENT, self).create(vals)

    name = fields.Char(
        'Description Reference',
        required=False,
        readonly=False,
        index=True,
        copy=False,
        default='New')
    candidate_email = fields.Char(
        'Candidate Email',
        required=True,
        readonly=False,
        index=True,
        copy=True,)
    candidate_name = fields.Char(
        'Candidate Name',
        required=True,
        readonly=False,
        index=True,
        copy=True,)
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
    
    users_followers = fields.Many2many(
        'hr.employee',
        string='Add followers',
        required=False,
        default=_get_all_followers)

    file_upload_employee_letter = fields.Binary('Upload Employement Letter') # HR HR Assistant'
    binary_fname = fields.Char('Binary Name')
    phone = fields.Char('Phone')
    file_upload_reject_outcome = fields.Binary('Rejection outcome Note') # HR Officer1
    binaryreject_fname = fields.Char('Binary Name')

    '''file_upload_app_budget = fields.Binary('Upload Approved Budget') # HR Manager1
    binaryappbudget_fname = fields.Char('Binary Name')

    file_upload_blueprint = fields.Binary('Upload Strategic Blueprint')
    binary_fname_blueprint = fields.Char('Binary Name')

    file_upload_activity_workplan = fields.Binary('Activity Workplan')
    binary_fname_activity_workplan = fields.Char('Binary Name')'''

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
    state = fields.Selection([('HR Officer1', 'HR Officer'),
                              ('HR Assistant', 'HR Assistant'),
                              ('HR manager1', 'HR Manager'),
                              ('GM', 'GM'),
                              ('HR manager2', 'HR Manager'),
                              ('HR Officer2', 'HR Officer'),
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
                              ('IT', 'Industrial Training')],
                            string='Type', required=True, index=True,
                            copy=True, default='Full Term',
                            track_visibility='onchange')
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='No. Attachments')
    
    
    # ##################################################### 
    
    @api.multi
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'hr.offer.management'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for rec in self:
            rec.attachment_number = attachment.get(rec.id, 0)
    @api.multi
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'hr.offer.management'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'hr.offer.management', 'default_res_id': self.id}
        return res
 
       
    @api.multi
    def button_rejects(self):
        
        if not self.description_two:
            raise ValidationError(
                'Please Add a Remark in the Refusal Note tab below')
        else:
            if self.state == "HR Assistant":
                self.state = "HR Officer1"
                self.reject_mail_hr_Assistant()
            elif self.state == "HR manager1":
                self.state = "HR Assistant"
                self.reject_mail_hrmanager()
            elif self.state == "GM":
                self.state = "HR manager1"
                self.reject_mail_gm()
             
             

    @api.multi
    def reject_mail_hr_Assistant(self, force=False):  #  draft 
        email_from = self.env.user.login
        group_user_id = self.env.ref('hr.group_hr_user').id
        bodyx = "Dear Sir, <br/>A Manpower Budget have been Rejected by \
        the HR Assistant manager\
        Kindly {} to view. <br/>\
        Regards".format(self.get_url(self.id, self._name))
        self.mail_sending_reject(email_from, group_user_id, bodyx)

    @api.multi
    def reject_mail_hrmanager(self, force=False):  #  draft 
        email_from = self.env.user.login
        group_user_id = self.env.ref('hr.group_hr_manager').id
        bodyx = "Dear Sir, <br/>A Manpower Budget have been Rejected by \
        the HR manager\
        Kindly {} to view. <br/>\
        Regards".format(self.get_url(self.id, self._name))
        self.mail_sending_reject(email_from, group_user_id, bodyx)

    @api.multi
    def reject_mail_gm(self, force=False):  #  draft 
        email_from = self.env.user.login
        group_user_id = self.env.ref('hr.group_hr_manager').id
        bodyx = "Dear Sir, <br/>A Manpower Budget have been Rejected by \
        the GM\
        Kindly {} to view. <br/>\
        Regards".format(self.get_url(self.id, self._name))
        self.mail_sending_reject(email_from, group_user_id, bodyx)

     
    # ##################### HR ASSISTANCE SEND MAIL TO HODs #################
    @api.one
    def send_to_memo_hods(self):
        self.write({'state': 'HOD', 'description_two':''})
        return self.send_hods_mail()
    @api.multi
    def send_hods_mail(self, force=False):
        email_from = self.env.user.company_id.email
        group_user_id = self.env.ref('ikoyi_module.ikoyi_hod').id
        subject = "Ikoyi Club HR Notification"
        bodyx = "Dear Sir, <br/>All HODs are requested to submit their manpowers plans.\
            Kindly {} to view. <br/>\
            Regards".format(self.get_url(self.id, self._name))
        filename = self.file_upload_employee_letter
        self.mail_sending_attachment(email_from, group_user_id, bodyx, 
                                     subject, filename)

    # ############################### Send All Remainders BUTTONS ######################
    
    @api.one
    def send_to_reminder_to_all(self):
        return self.send_mail_remainder()

    def send_mail_remainder(self):
        bodyx = "Dear Sir, <br/>This is to remind all HODs for the request to submit their manpowers plans.\
        Kindly {} to view. <br/>\
        Regards".format(self.get_url(self.id, self._name))
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.ikoyi_hod').id
        group_user_id = self.env.ref('hr.group_hr_manager').id
        group_user_id3 = self.env.ref('hr.group_hr_user').id

        if self.id:
            bodyx = bodyx
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyx) 
        else:
            raise ValidationError('No Record created')
        
    # ##################### HR ASSISTANCE SEND MAIL TO HODs #################

    @api.one
    def hr_officer_to_hr_assistant(self): #  HR Officer
        self.write({'state': 'HR Assistant', 'description_two': ''})
        return self.send_mail1()
    @api.multi
    def send_mail1(self, force=False):
        email_from = self.env.user.company_id.email
        group_user_id = self.env.ref('hr.group_hr_manager').id
        subject = "HR Offer Notification"
        bodyx = "Dear Sir, <br/>This is to inform you that an Employment letter have been sent\
        to you for review and approval. <br/>\
        Kindly {} <br/>\
        Regards".format(self.get_url(self.id, self._name))
        filename = self.file_upload_employee_letter
        self.mail_sending_attachment(email_from, group_user_id, bodyx, 
                                     subject, filename)
        
    @api.one
    def hr_assistant_approve(self):#  HR Officer
        self.write({'state': 'HR manager1', 'description_two':''})
        return self.send_mail2()
    @api.multi
    def send_mail2(self, force=False):
        email_from = self.env.user.company_id.email
        group_user_id = self.env.ref('hr.group_hr_manager').id
        subject = "HR Offer Notification"
        bodyx = "Dear Sir, <br/>This is to inform you that an Employment letter have been sent\
        to you for review and approval. <br/>\
        Kindly {}<br/>\
        Regards".format(self.get_url(self.id, self._name))
        filename = self.file_upload_employee_letter
        self.mail_sending_attachment(email_from, group_user_id, bodyx, 
                                     subject, filename)
        
    @api.one
    def hr_manager_approve(self):#  HR manager1
        self.write({'state': 'GM', 'description_two':''})
        return self.send_mail3()
    @api.multi
    def send_mail3(self, force=False):
        email_from = self.env.user.company_id.email
        group_user_id = self.env.ref('ikoyi_module.gm_ikoyi').id
        subject = "HR Offer Notification"
        bodyx = "Dear Sir, <br/>This is to inform you that an Employment letter have been sent\
        to you for review and approval. <br/>\
        Kindly {}<br/>\
        Regards".format(self.get_url(self.id, self._name))
        filename = self.file_upload_employee_letter
        self.mail_sending_attachment(email_from, group_user_id, bodyx, 
                                     subject, filename)
        
    @api.one
    def gm_approve(self): #GM
        self.write({'state': 'HR manager2', 'description_two': ''})
        return self.send_mail4()

    def send_mail4(self, force=False):
        email_from = self.env.user.company_id.email
        group_user_id = self.env.ref('hr.group_hr_manager').id
        bodyx = "Dear Sir, <br/>This is to inform you that an Employment \
        letter have been approved by the General Manager.\
        <br/>Kindly Proceed with the necessary procesess. <br/> \
        Kindly {} to view. <br/>\
        Regards".format(self.get_url(self.id, self._name))
        self.mail_sending(email_from, group_user_id, bodyx)
   
    @api.one
    def hrmanager2_approve(self):
        self.write({'state': 'HR Officer2', 'description_two': ''})
        return self.send_mail_offer()

    def send_mail_offer(self, force=False):
        email_from = self.env.user.company_id.email
        group_user_id = self.env.ref('hr.group_hr_manager').id
        bodyx = "Dear Sir, <br/>This is to inform you that an Employment \
        letter have been approved by the General Manager.\
        <br/>Kindly Proceed to contact the candidate for employment. <br/> \
        Also {} to view. <br/>\
        Regards".format(self.get_url(self.id, self._name))
        self.mail_sending(email_from, group_user_id, bodyx)

    @api.one
    def hrofficer_to_candidate(self):
        self.write({'state': 'Waiting', 'description_two': ''})
        return self.send_mail5()

    def send_mail5(self, force=False):
        email_from = self.env.user.company_id.email
        mail_to = self.candidate_email
        bodyx = "Dear, <br/>This is to inform you that you that an Offer of Employment \
        have been given to you at Ikoyi Club 1938. <br/> Kindly go to the {} department to indicate your interest. \
        Kindly {} to view. <br/>\
        Regards".format(self.department_id.name, self.get_url(self.id, self._name))

        self.mail_sending_candidate(email_from, mail_to, bodyx)

    @api.one
    def set_candidate_reject(self):
        if not self.file_upload_reject_outcome:
            raise ValidationError('please Upload the rejection outcome note')
        else:
            self.state = "Rejected"
            
            email_from = self.env.user.company_id.email
            group_user_id = self.env.ref('hr.group_hr_manager').id
            subject = "Ikoyi Club HR Notification"        
            bodyx = "Dear Sir, <br/>This is to inform all HODs / Admins\
            that the Offer Employement with Reference {} has been rejected by the candidate \
            Kindly {} to view the outcome of the rejection. <br/>\
            Regards".format(self.name, self.get_url(self.id, self._name))
            filename = self.file_upload_employee_letter
            return self.sendmail_to_followers(email_from, group_user_id, bodyx,
                                            subject, filename)
 
    @api.one
    def set_candidate_accepted(self):
        self.state = "Accepted"
        return self.mail_candidate_accept_followers()
    
    def mail_candidate_accept_followers(self):
        email_from = self.env.user.company_id.email
        group_user_id = self.env.ref('hr.group_hr_manager').id
        subject = "Ikoyi Club HR Notification"
        bodyx = "Dear Sir, <br/>This is to inform all HODs / Admins\
        that the Offer Employement with Reference {} has been accepted by the candidate \
        Kindly {} to view. <br/>\
        Regards".format(self.name, self.get_url(self.id, self._name))
        filename = self.file_upload_employee_letter
        self.sendmail_to_followers(email_from, group_user_id, bodyx, subject, filename)

    def send_mail_accept_reject(self, bodyc):

        email_from = self.env.user.email
        group_user_id2 = self.env.ref('hr.group_hr_assistant').id
        group_user_id = self.env.ref('hr.group_hr_manager').id
        group_user_id3 = self.env.ref('ikoyi_module.gm_ikoyi').id

        if self.id:
            bodyc = bodyc
            self.mail_sending_for_three(
                email_from,
                group_user_id,
                group_user_id2,
                group_user_id3,
                bodyc) 
        else:
            raise ValidationError('No Record created')

    @api.multi
    def print_employee_form(self):
        self.state = "Complete"
        return self.env['report'].get_action(self, 'ikoyi_module.print_grn_template')

    # @api.multi
    # def create_employee(self): # complete
    #     view = self.env.ref('hr.view_employee_form')
    #     view_id = view and view.id or False
    #     context = dict(self._context or {})
    #     return {'name': 'Employee Creation',
    #                 'type': 'ir.actions.act_window',
    #                 'view_type': 'form',
    #                 'res_model': 'hr.employee',
    #                 'views': [(view.id, 'form')],
    #                 'view_id': view.id,
    #                 'target': 'current',
    #                 'context': {'default_name': self.phone,#self.candidate_name, 
    #                             'default_work_email': self.candidate_email,
    #                             'default_department_id': self.department_id.id,
    #                             'default_mobile_phone': self.phone
    #                             },                  
    #             }  
        
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

    # ############################################################
    @api.onchange('candidate_name')
    def _onchange_name(self):
        if self.candidate_name:
            self.candidate_name = self.candidate_name.strip()
            
    @api.constrains('phone', 'candidate_email')
    def _check_dependant(self):
        if self.phone:
            phone_valid = self.phone.strip().isdigit()
            if phone_valid:
                pass
            else:
                raise ValidationError('Please input the correct phone Number')

        if self.candidate_email:
            rematch = re.match("^.+@(\[?)[a-zA-Z0-9-.]+.([a-zA-Z]{2,3}|[0-9]{1,3})(]?)$", self.candidate_email, re.IGNORECASE)
            if rematch != None:
                pass
            else:
                raise ValidationError('Please input the correct Email Address')

    def sendmail_to_followers(self, email_from, group_user_id, bodyx, subject, filename):
        lists = []
        # save pdf as attachment 
        ATTACHMENT_NAME = "NOTE"
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
            
    ##################################################
    def mail_sending(self, email_from, group_user_id, bodyx):
        from_browse = self.env.user.name
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

            email_froms = str(from_browse) + " <" + str(email_from) + ">"
            mail_appends = (', '.join(str(item)for item in followers))
            mail_to = (','.join(str(item2)for item2 in email_to))
            subject = "HR Notification"
            # extrax = (', '.join(str(extra)))
            # followers.append(extrax)
            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': mail_to,
                'email_cc': mail_appends,  #  + (','.join(str(extra)),
                'reply_to': email_from,
                'body_html': bodyx
            }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)
    
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

    def mail_sending_attachment(self, email_from, group_user_id, bodyx, 
                                subject, filename):
        lists = []
        # save pdf as attachment 
        ATTACHMENT_NAME = "NOTE"
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

    def mail_sending_reject(self, email_from, group_user_id, bodyx):
        from_browse = self.env.user.name
        groups = self.env['res.groups']
        for order in self:
            group_users = groups.search([('id', '=', group_user_id)])
            group_emails = group_users.users
            email_to = []

            for gec in group_emails:
                email_to.append(gec.login)

            email_froms = "Ikoyi Club" + " <" + str(email_from) + ">"
            mail_to = (','.join(str(item2)for item2 in email_to))
            subject = "HR REFUSAL Notification"

            # extrax = (', '.join(str(extra)))
            # followers.append(extrax)
            mail_data = {
                'email_from': email_froms,
                'subject': subject,
                'email_to': mail_to,
                # 'email_cc': mail_appends,  #  + (','.join(str(extra)),
                'reply_to': email_from,
                'body_html': bodyx
            }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)
