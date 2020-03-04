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


class HR_Capital_Development(models.Model):
    _name = "hr.capital.development"
    _inherit = ['mail.thread'] #, 'ir.needaction_mixin']
    _description = "Human Resource Capital Development"
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

        hr_manager_group = groups.search([('id', '=', hr_manager)])
        chairman_group = groups.search([('id', '=', chairman)])
        vc_group = groups.search([('id', '=', vice_chairman)])
        gm_group = groups.search([('id', '=', general_manager)])

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

        return followers

    READONLY_STATES = {
        'HR manager': [('readonly', True)],
        'Executive': [('readonly', True)],
        'GM': [('readonly', True)],
        'HR manager4': [('readonly', True)],
        'HR manager2': [('readonly', True)],
        'HR manager3': [('readonly', True)],
        'IRC': [('readonly', True)],



    }

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('hr.capital.development')
        vals['name'] = str(sequence)
        return super(HR_Capital_Development, self).create(vals)

    name = fields.Char(
        'Description Reference',
        required=False,
        readonly=True,
        index=True,
        copy=False,
        default='New')
    branch_id = fields.Many2one(
        'res.branch',
        string="Section",
        default=lambda self: self.env.user.branch_id.id,
        help="Tell Admin to set your branch... \
        (Users-->Preferences-->Allowed Branch)")

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

    users_followers = fields.Many2many(
        'hr.employee',
        string='Add followers',
        required=False,
        default=_get_all_followers)

    file_upload = fields.Binary('Upload Strategic Direction')
    binary_fname = fields.Char('Binary Name')

    file_upload_blueprint = fields.Binary('Upload Strategic Blueprint')
    binary_fname_blueprint = fields.Char('Binary Name')

    file_upload_activity_workplan = fields.Binary('Activity Workplan')
    binary_fname_activity_workplan = fields.Char('Binary Name')

    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        index=True,
        states=READONLY_STATES,
        default=lambda self: self.env.user.company_id.id)
    state = fields.Selection([('HR Officer1', 'HR Officer'),
                              ('HR manager', 'HR Manager'),
                              ('Executive', 'Executive Team'),
                              ('GM', 'GM'),
                              ('HR manager2', 'HR Manager'),
                              ('HR Officer2', 'HR Officer'),
                              ('HR manager3', 'HR Manager'),
                              ('IRC', 'IRSC'),
                              ('HR manager4', 'HR Manager'),
                              ('HOD', 'HODs'),
                              ('refuse', 'refuse')],
                             string='Status', readonly=True, index=True,
                             copy=False, default='HR Officer1',
                             track_visibility='onchange')

    employee_id = fields.Many2one(
        'hr.employee', states=READONLY_STATES,
        string='Employee',
        required=True,
        default=_default_employee)

    notes = fields.Text('Terms and Conditions')

    description_two = fields.Text('Refusal Reasons')
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='No. Attachments')

    # ##################################################### 
    
    @api.multi
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'hr.capital.development'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for rec in self:
            rec.attachment_number = attachment.get(rec.id, 0)
    @api.multi
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'hr.capital.development'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'hr.capital.development', 'default_res_id': self.id}
        return res

    
    # #####################################################    
    @api.multi
    def button_rejects(self):
        if not self.description_two:
            raise ValidationError(
                'Please Add a Remark in the Refusal Note tab below')
        else:
            if self.state == "HR manager":
                self.state = "HR Officer1"
                self.reject_mail_hr_manager1()
            elif self.state == "Executive":
                self.state = "HR manager"
                self.reject_mail_executive()
            elif self.state == "HR manager3":
                self.state = "HR Officer2"
                self.reject_mail_hrmanager3()

            elif self.state == "IRC":
                self.state = "HR manager3"
                self.reject_mail_irc()

    @api.multi
    def reject_mail_hr_manager1(self, force=False):  #  draft 
        email_from = self.env.user.login
        group_user_id = self.env.ref('hr.group_hr_user').id
        bodyx = "Dear Sir, <br/>A Strategy Blueprint have been Rejected by the HR manager\
            Kindly {} to view. <br/>\
            Regards".format(self.get_url(self.id, self._name))
        self.mail_sending_reject(email_from, group_user_id, bodyx)

    @api.multi
    def reject_mail_executive(self, force=False):  #  draft 
        email_from = self.env.user.login
        group_user_id = self.env.ref('hr.group_hr_manager').id
        bodyx = "Dear Sir, <br/>A Strategy Blueprint have been Rejected by the Executive members.\
            Kindly {} to view. <br/>\
            Regards".format(self.get_url(self.id, self._name))
        self.mail_sending_reject(email_from, group_user_id, bodyx)

    @api.multi
    def reject_mail_irc(self, force=False):  #  draft 
        email_from = self.env.user.login
        group_user_id = self.env.ref('hr.group_hr_manager').id
        bodyx = "Dear Sir, <br/>A Strategy Blueprint have been Rejected by the IRSC\
            Kindly {} to view. <br/>\
            Regards".format(self.get_url(self.id, self._name))
        self.mail_sending_reject(email_from, group_user_id, bodyx)

    @api.multi
    def reject_mail_hrmanager3(self, force=False):  #  draft 
        email_from = self.env.user.login
        group_user_id = self.env.ref('hr.group_hr_user').id
        bodyx = "Dear Sir, <br/>An Activity Workplan have been Rejected by the HR manager\
            Kindly {} to view. <br/>\
            Regards".format(self.get_url(self.id, self._name))
        self.mail_sending_reject(email_from, group_user_id, bodyx)

    @api.one
    def send_to_hr(self):
        self.write({'state': 'HR manager', 'description_two':''})
        return self.send_hr_manager_mail()
    @api.multi
    def send_hr_manager_mail(self, force=False):
        email_from = self.env.user.company_id.email
        group_user_id = self.env.ref('hr.group_hr_manager').id
        subject = "Ikoyi Club HR Notification"
        bodyx = "Dear Sir, <br/>A Strategy Blueprint have been sent for your confirmation.\
            Kindly {} to view. <br/>\
            Regards".format(self.get_url(self.id, self._name))
        filename = self.file_upload
        self.mail_sending_attachment(email_from, group_user_id, bodyx, 
                                     subject, filename)
    # ############################### EXECUTIVE BUTTONS ######################
    @api.one
    def send_to_executive(self):
        self.write({'state': 'Executive', 'description_two': ''})
        return self.send_mail_executive()

    def send_mail_executive(self):
        bodyx = "Dear Sir, <br/>A Strategy Blueprint have been sent to \
        Executive Managements for confirmation.\
        Kindly {} to view. <br/>\
        Regards".format(self.get_url(self.id, self._name))
        email_from = self.env.user.email
        group_user_id2 = self.env.ref('ikoyi_module.executive_management_ikoyi').id
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

    # ############################### GM BUTTONS ############################
    '''@api.one
    def send_to_gm(self):
        self.write({'state': 'GM'})
        return self.sendmail_gm()

    def sendmail_gm(self, force=False):
        email_from = self.env.user.company_id.email
        group_user_id = self.env.ref('ikoyi_module.gm_ikoyi').id

        bodyx = "Dear Sir, <br/>A Strategy Blueprint have been sent to \
        you for confirmation.\
        Kindly {} to view. <br/>\
        Regards".format(self.get_url(self.id, self._name))
        self.mail_sending(email_from, group_user_id, bodyx)'''

    # ############################### HR2 BUTTONS ############################
    # @api.one
    # def send_gm_hr2(self):
    #     self.write({'state': 'HR manager2', 'description_two': ''})
    #     return self.sendmail_hr2()
    
    @api.one
    def send_gm_hr2(self):
        self.write({'state': 'GM', 'description_two': ''})
        return self.sendmail_hr2()

    def sendmail_hr2(self, force=False):
        email_from = self.env.user.company_id.email
        group_user_id = self.env.ref('hr.group_hr_manager').id
        bodyx = "Dear Sir, <br/>A Strategy Blueprint have been sent to \
        you for confirmation.\
        Kindly {} to view. <br/>\
        Regards".format(self.get_url(self.id, self._name))
        self.mail_sending(email_from, group_user_id, bodyx)

    # ############################### HR2 APPROVE BUTTONS #####################

    @api.one
    def send_to_hr_officer(self):
        self.write({'state': 'HR Officer2', 'description_two': ''})
        return self.sendmail_hrofficer()

    def sendmail_hrofficer(self, force=False):
        email_from = self.env.user.company_id.email
        group_user_id = self.env.ref('hr.group_hr_user').id
        # extra = self.env.user.email
        bodyx = "Dear Sir, <br/>A Strategy Blueprint have been sent to \
        you for confirmation.\
        Kindly {} to view. <br/>\
        Regards".format(self.get_url(self.id, self._name))
        self.mail_sending(email_from, group_user_id, bodyx)

    # #################### HR Officer Workflow Activity #####################

    @api.one
    def send_to_hr_manager3(self):
        self.write({'state': 'HR manager3', 'description_two': ''})
        return self.sendmail_hr2()

    def sendmail_hrofficer(self, force=False):
        email_from = self.env.user.company_id.email
        group_user_id = self.env.ref('hr.group_hr_manager').id
        # extra = self.env.user.email
        bodyx = "Dear Sir, <br/>An Activity Workplan have been sent to \
        you for confirmation.\
        Kindly {} to view. <br/>\
        Regards".format(self.get_url(self.id, self._name))
        self.mail_sending(email_from, group_user_id, bodyx)

    # ############## HR Manager approve Workflow Activity to ICR ##############
    @api.one
    def manager_send_to_irc(self):
        self.write({'state': 'IRC', 'description_two': ''})
        return self.send_hr_to_irc()

    @api.multi
    def send_hr_to_irc(self, force=False):
        email_from = self.env.user.company_id.email
        group_user_id = self.env.ref('ikoyi_module.irc_ikoyi').id
        subject = "Ikoyi Club HR Notification"
        bodyx = "Dear Sir, <br/>An Activity Workplan have been sent for your confirmation.\
            Kindly {} to view. <br/>\
            Regards".format(self.get_url(self.id, self._name))
        filename = self.file_upload_activity_workplan
        self.mail_sending_attachment(email_from, group_user_id, bodyx, 
                                     subject, filename)

    # #################### VICE CHAIRMAN APPROVE Workflow Activity #########
    @api.one
    def send_to_hr4(self):
        self.write({'state': 'HR manager4', 'description_two': ''})
        return self.sendmail_hrmanager4()

    def sendmail_hrmanager4(self, force=False):
        email_from = self.env.user.company_id.email
        group_user_id = self.env.ref('hr.group_hr_manager').id
        # extra = self.env.user.email
        bodyx = "Dear Sir, <br/>An Activity Workplan have been sent to \
        you for circulation.\
        Kindly {} to view. <br/>\
        Regards".format(self.get_url(self.id, self._name))
        self.mail_sending(email_from, group_user_id, bodyx)

    # ############## HR Manager sends to All HOU ##############
    @api.one
    def send_to_hod(self):
        self.write({'state': 'HOD', 'description_two': ''})
        return self.send_hr_to_hou()

    @api.multi
    def send_hr_to_hou(self, force=False):
        email_from = self.env.user.company_id.email
        group_user_id = self.env.ref('ikoyi_module.ikoyi_hod').id
        subject = "Ikoyi Club HR Notification"
        bodyx = "Dear Sir, <br/>An Activity Workplan have been sent for your review.\
            Kindly {} to view. <br/>\
            Regards".format(self.get_url(self.id, self._name))
        filename = self.file_upload_activity_workplan
        self.mail_sending_attachment(email_from, group_user_id, bodyx,
                                     subject, filename)

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
