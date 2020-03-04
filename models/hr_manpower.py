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


class HR_ManPower(models.Model):
    _name = "hr.manpower"
    _inherit = ['mail.thread', 'ir.attachment'] #, 'ir.needaction_mixin']
    _description = "Human Resource Manpower and Recruitment"
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
        chairman = self.env.ref('ikoyi_module.chairman_ikoyi').id
        vice_chairman = self.env.ref('ikoyi_module.vice_chairman_ikoyi').id
        general_manager = self.env.ref('ikoyi_module.gm_ikoyi').id
        hod_manager = self.env.ref('ikoyi_module.ikoyi_hod').id
        hou_manager = self.env.ref('ikoyi_module.ikoyi_hou').id
        hr_user = self.env.ref('hr.group_hr_user').id

        hr_manager_group = groups.search([('id', '=', hr_manager)])
        chairman_group = groups.search([('id', '=', chairman)])
        vc_group = groups.search([('id', '=', vice_chairman)])
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

        for rec in chairman_group:
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
        'HR Assitant2': [('readonly', True)],
        'HR manager1': [('readonly', True)],
    }

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('hr.manpower')
        vals['name'] = str(sequence)
        return super(HR_ManPower, self).create(vals)

    name = fields.Char(
        'Description Reference',
        required=False,
        index=True,
        copy=False,
        default='New')
    user_id = fields.Many2one(
        'res.users',
        string="Users", readonly=True,
        default=lambda a: a.env.user.id)

    date_order = fields.Datetime(
        'Date',
        required=True,
        states=READONLY_STATES,
        index=True,
        copy=False,
        default=fields.Datetime.now)
    date_deadline = fields.Datetime(
        'Date',
        required=True,
        states=READONLY_STATES,
        index=True,
        copy=False)

    users_followers = fields.Many2many(
        'hr.employee',
        string='Add followers',
        required=False,
        default=_get_all_followers)

    file_upload_memo = fields.Binary('Upload Memo Document') # HR Assitant
    binary_fname = fields.Char('Binary Name')
    
    file_upload_budget = fields.Binary('Upload Manpower Budget') # HR Officer1
    binarybudget_fname = fields.Char('Binary Name')

    file_upload_app_budget = fields.Binary('Upload Approved Budget') # HR Manager1
    binaryappbudget_fname = fields.Char('Binary Name')

    '''file_upload_blueprint = fields.Binary('Upload Strategic Blueprint')
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
    state = fields.Selection([('HR Assitant', 'HR Assistant'),
                              ('HOD', 'HODs'),
                              ('HR Officer1', 'HR Officer'),
                              ('HR Assitant2', 'HR Assistant'),
                              ('HR manager1', 'HR Manager'),
                              ('Complete', 'Complete'),
                              ('refuse', 'refuse')],
                             string='Status', readonly=True, index=True,
                             copy=False, default='HR Assistant',
                             track_visibility='onchange')

    employee_id = fields.Many2one(
        'hr.employee', states=READONLY_STATES,
        string='Employee',
        required=True,
        default=_default_employee)

    notes = fields.Text('Terms and Conditions')

    description_two = fields.Text('Refusal Reasons')
    
    # #####################################################    
    @api.multi
    def button_rejects(self):
        
        if not self.description_two:
            raise ValidationError(
                'Please Add a Remark in the Refusal Note tab below')
        else:
            if self.state == "HR Assitant2":
                self.state = "HR Officer1"
                self.reject_mail_hr_Assistant()
            elif self.state == "HR manager1":
                self.state = "HR Assitant2"
                self.reject_mail_hrmanager()
             

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
        the HR Assistant manager\
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
        filename = self.file_upload_memo
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
    def send_to_hrofficer(self):
        self.write({'state': 'HR Officer1', 'description_two':''})
        return self.send_hrofficer_mail()
    @api.multi
    def send_hrofficer_mail(self, force=False):
        email_from = self.env.user.company_id.email
        group_user_id = self.env.ref('hr.group_hr_user').id
        subject = "Ikoyi Club HR Notification"
        bodyx = "Dear Sir, <br/>This is to inform you that all departments \
        have submitted their manpowers plannings.\ <br/> Please Proceed with the\
        development of budget plans. <br/>\
        Kindly {} to view. <br/>\
        Regards".format(self.get_url(self.id, self._name))
        filename = self.file_upload_memo
        self.mail_sending_attachment(email_from, group_user_id, bodyx, 
                                     subject, filename)
        
    @api.one
    def send_to_hrAssitant2(self):
        self.write({'state': 'HR Assitant2', 'description_two':''})
        return self.send_hrassitant2_mail()
    
    @api.multi
    def send_hrassitant2_mail(self, force=False):
        email_from = self.env.user.company_id.email
        group_user_id = self.env.ref('hr.group_hr_manager').id
        subject = "Ikoyi Club HR Notification"
        bodyx = "Dear Sir, <br/>This is to inform you that budget plans have been developed \
        and waiting for your approval.<br/>\
        Kindly {} to view. <br/>\
        Regards".format(self.get_url(self.id, self._name))
        filename = self.file_upload_budget
        self.mail_sending_attachment(email_from, group_user_id, bodyx, 
                                     subject, filename) 
        
    @api.one
    def send_hrassit_hmmanager(self):
        self.write({'state': 'HR manager1', 'description_two': ''})
        return self.sendmail_hr2()

    def sendmail_hr2(self, force=False):
        email_from = self.env.user.company_id.email
        group_user_id = self.env.ref('hr.group_hr_manager').id
        bodyx = "Dear Sir, <br/>This is to inform you that budget plans have been developed \
        and waiting for your approval.<br/>\
        Kindly {} to view. <br/>\
        Regards".format(self.get_url(self.id, self._name))
        self.mail_sending(email_from, group_user_id, bodyx)
        
    @api.one
    def send_approvebudget_hods(self):
        self.write({'state': 'Complete', 'description_two':''})
        return self.send_hods_mail()
    @api.multi
    def send_hods_mail(self, force=False):
        email_from = self.env.user.company_id.email
        group_user_id = self.env.ref('ikoyi_module.ikoyi_hod').id
        subject = "Ikoyi Club HR Notification"
        bodyx = "Dear Sir, <br/>All HODs are to be informed that the manpowers budget plans.\
            have been approve by the budget committee \
            Kindly {} to view. <br/>\
            Regards".format(self.get_url(self.id, self._name))
        filename = self.file_upload_app_budget
        self.mail_sending_attachment(email_from, group_user_id, bodyx, 
                                     subject, filename)

    @api.multi
    def print_mandate_pop(self):
        # return self.env['report'].get_action(self, 'ikoyi_module.print_singlemandate_template')
        popup_message = "PLEASE KINDLY CLICK ON THE 'Upload Approved Budget' FIELD TO DOWNLOAD"
        return self.popup_notification(popup_message)
         
    def popup_notification(self, popup_message):
        view = self.env.ref('sh_message.sh_message_wizard')
        view_id = view and view.id or False
        context = dict(self._context or {})
        context['message'] = popup_message # 'Successful'
        return {'name':'Alert!',
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'res_model': 'sh.message.wizard',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'context': context,
                }  

    
    # ############################################################

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
            bodyxx = "Dear Sir/Madam, <br/>We wish to notify you that a GRO \
            from {} has been sent to you for approval <br/> <br/>Kindly \
            review it.</br> <br/>Thanks".format(self.employee_id.name)
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
