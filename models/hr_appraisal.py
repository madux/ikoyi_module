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


class HRAppraisalSection(models.Model):
    _name = 'ikoyi.appraisal.section'
    name = fields.Char(string="Enter KPI Question", required=True)


class HRAppraisalConfig(models.Model):
    _name = 'ikoyi.appraisal.config'

    name = fields.Char(string="Enter KPI Question")
    target = fields.Float(string="Target(%)")
    weight = fields.Float(string="Weight")
    section = fields.Many2one('ikoyi.appraisal.section', required=True, string="Section")


class HRAppraisalTemplate(models.Model):
    _name = 'ikoyi.appraisal.template'

    question_id = fields.Many2one('ikoyi.appraisal.config', string='KPI')
    section = fields.Many2one('ikoyi.appraisal.section', required=True, string="Section")
    line_id = fields.Many2one('ikoyi.appraisal', string='Aprraisal ID')
    target = fields.Float(string="Target(%)", store=True)
    weight = fields.Float(string="Weight", store=True)
    note = fields.Text(string="Note")
    hr_employee_score = fields.Float(string="Employee score")
    unit_manager_score = fields.Float(string="HOU score")
    hod_score = fields.Float(string="HOD score")
    state = fields.Selection([('draft', 'Draft'),
                              ('hr_manager', 'Hr Manager'),
                              ('sent', 'Employee'),
                              ('unit_manager', 'Unit Manager'),
                              ('hod', 'HOD'),
                              ('hr_manager_two', 'Hr Manager'),
                              ('gm', 'GM'),
                            #   ('hod', 'HOD'),
                              ('hr_manager_three', 'Done'),
                              ('refuse', 'Refuse')],
                             string='State',
                             copy=True, compute="compute_line_id",
                             track_visibility='onchange')


    # @api.depends('weight')
    # def cal_scores_limit(self):
    #     if self.hr_employee_score > self.weight:
    #         raise ValidationError('Your score is above the limit')

    #     elif self.unit_manager_score > self.weight:
    #         raise ValidationError('Your score is above the limit')

    #     elif self.hod_score > self.weight:
    #         raise ValidationError('Your score is above the limit')
        
    #     else:
    #         pass








    @api.onchange('section')
    def domain_section_question(self):
        sections = self.env['ikoyi.appraisal.config'].search([('section', '=', self.section.id)])
        domain = {'question_id': [('id', '=', [s.id for s in sections if sections])]}
        return {'domain': domain}

    @api.onchange('question_id')
    def domain_questionaire(self):
        if self.question_id:
            self.target =self.question_id.target
            self.weight =self.question_id.weight

    @api.one
    @api.depends('line_id')
    def compute_line_id(self):
        if self.line_id:
            self.state = self.line_id.state
            
    @api.multi
    def unlink(self):
        for record in self.filtered(lambda record: record.state not in ['draft','refuse']):
            raise ValidationError(_('In order to delete an Appraisal line, you must cancel it first...'))
        return super(HRAppraisalTemplate, self).unlink()


class HRAppraisal(models.Model):
    _name = 'ikoyi.appraisal'
    _rec_name = "subject"
    
    subject = fields.Char('Subject', required=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('hr_manager', 'Hr Manager'),
                              ('sent', 'Employee'),
                              ('unit_manager', 'Unit Manager'),
                              ('hod', 'HOD'),
                              ('hr_manager_two', 'Hr Manager'),
                              ('gm', 'GM'),
                            #   ('hod', 'HOD'),
                              ('hr_manager_three', 'Done'),
                              ('refuse', 'Refuse')],
                             string='State',
                             copy=True, default='draft',
                             track_visibility='onchange')
    """
    Template field will be added here. It should also be on a questionaire tab 
    """
    appraisal_line = fields.One2many('ikoyi.appraisal.template', 'line_id',
                                     string="Appraisal Line")
    employee_id = fields.Many2one('hr.employee', string='Employee Name')
    dept_ids = fields.Char(string='Department',
                           related='employee_id.department_id.name',
                           readonly=True,
                           store=True)
    
    employment_date = fields.Date(string='Employment Date')
    appr_date = fields.Date(string='Appraisal Date', default=fields.Date.today())
    
    lst_promo_date = fields.Date(string='Last Promotion Date')
    job_title = fields.Char(string='Job title',
                            related='employee_id.job_id.name',
                            readonly=True,
                            store=True)
    
    reviewer_name = fields.Char(string="Reviewer's Name")
    total_average_score = fields.Float(string="Total Average score", compute="average_calculator")
    hr_comment = fields.Text(string="HR Comment")
    gm_comment = fields.Text(string="GM Comment")
    training_need = fields.Text(string="HR Comment")
    area_of_improvement = fields.Text(string="Area of Self Improvement")
    note = fields.Text(string="Note")
    emp_total_score = fields.Float(string="Employee Total Score", compute="sub_total_score")
    unit_total_score = fields.Float(string="Unit Manager Score", compute="sub_total_score")
    hod_total_score = fields.Float(string="HOD Total Score", compute="sub_total_score")
    #total_score = fields.Float(string="Total Score", compute="total_score")


    @api.multi
    def unlink(self):
        for record in self.filtered(lambda record: record.state not in ['draft','refuse']):
            raise ValidationError(_('In order to delete an Appraisal line, you must cancel it first...'))
        return super(HRAppraisal, self).unlink()
    
    # @api.constrains('hod_score','hr_employee_score','unit_manager_score')
    def check_fields(self):
        errors = []
        limit_score1 = self.mapped('appraisal_line').filtered(lambda s: s.hr_employee_score > s.weight)
        limit_score2 = self.mapped('appraisal_line').filtered(lambda s: s.unit_manager_score > s.weight)
        limit_score3 = self.mapped('appraisal_line').filtered(lambda s: s.hod_score > s.weight)
        if self.state == "sent":
            employee_score = self.mapped('appraisal_line').filtered(lambda s: s.hr_employee_score == 0)
            if employee_score:
                errors.append('You must add the Employee score')
            elif limit_score1:
                errors.append('Your score is above the expected limit')
        if self.state == "unit_manager":
            hou_score = self.mapped('appraisal_line').filtered(lambda s: s.unit_manager_score == 0)
            if hou_score:
                errors.append('You must add the HOU score')
            elif limit_score2:
                errors.append('Your score is above the expected limit')
        if self.state == "hod":
            hods_score = self.mapped('appraisal_line').filtered(lambda s: s.hod_score == 0)
            if hods_score:
                errors.append('You must add the HOD score')
            elif limit_score3:
                errors.append('Your score is above the expected limit')
        if len(errors) > 0:
            raise ValidationError('\n'.join(errors))

    @api.one
    @api.depends('appraisal_line.unit_manager_score', 'appraisal_line.hod_score', 'appraisal_line.hr_employee_score')
    def sub_total_score(self):
        self.emp_total_score, self.hod_total_score, self.unit_total_score = 0, 0, 0
        for rep in self.appraisal_line:
            self.hod_total_score += rep.hod_score
            self.unit_total_score += rep.unit_manager_score
            self.emp_total_score += rep.hr_employee_score

    @api.multi
    @api.depends('emp_total_score', 'hod_total_score', 'unit_total_score')
    def cal_total_score(self):
        for tec in self:
            total_scorex = tec.emp_total_score + tec.unit_total_score + tec.hod_total_score
            self.total_score = total_scorex

    
              
    @api.one
    @api.depends('appraisal_line.unit_manager_score', 'appraisal_line.hod_score', 'appraisal_line.hr_employee_score')
    def average_calculator(self):
        average, hod_total, um_total, em_total = 0, 0, 0, 0
        for rec in self.appraisal_line:
            hod_total += rec.hod_score
            um_total += rec.unit_manager_score
            em_total += rec.hr_employee_score
            total = em_total + um_total + hod_total
            average = total / 3
        self.total_average_score = average

    def send_hr_manager(self): # draft
        email_from = self.env.user.email
        mail_to = self.employee_id.work_email
        group_user_id = self.env.ref('hr.group_hr_manager').id
        if not mail_to:
            raise ValidationError('The employee to direct the mail to does not have a mail')
        else:
            self.mail_sending(email_from, group_user_id, mail_to)
            self.write({'state': 'hr_manager'})

    def send_to_employee(self):
        email_from = self.env.user.email
        mail_to = self.employee_id.work_email
        if not mail_to:
            raise ValidationError('The employee to direct the mail to does not have a mail')
        else:
            self.send_mail_to_one(email_from, mail_to)
            self.state = 'sent'

    def send_unit_manager(self):
        self.check_fields()
        
        email_from = self.env.user.email
        mail_to = self.employee_id.work_email
        group_user_id = self.env.ref('ikoyi_module.ikoyi_hou').id

        if not mail_to:
            raise ValidationError('The employee to direct the mail to does not have a mail')
        else:
            self.mail_sending(email_from, group_user_id, mail_to)
            self.write({'state': 'unit_manager'})

    def send_to_hod(self):
	self.check_fields()
        email_from = self.env.user.email
        mail_to = self.employee_id.work_email
        group_user_id = self.env.ref('ikoyi_module.ikoyi_hod').id
        if not mail_to:
            raise ValidationError('The employee to direct the mail to does not have a mail')
        else:
            self.mail_sending(email_from, group_user_id, mail_to)
            self.write({'state': 'hod'})

    def send_hr_manager_two(self):
        self.check_fields()
        email_from = self.env.user.email
        mail_to = self.employee_id.work_email
        group_user_id = self.env.ref('hr.group_hr_manager').id
        if not mail_to:
            raise ValidationError('The employee to direct the mail to does not have a mail')
        else:
            self.mail_sending(email_from, group_user_id, mail_to)
            self.write({'state': 'hr_manager_two'})

    def send_to_gm(self):
        email_from = self.env.user.email
        mail_to = self.employee_id.work_email
        group_user_id = self.env.ref('ikoyi_module.gm_ikoyi').id
        self.mail_sending(email_from, group_user_id, mail_to)
        self.write({'state': 'gm'})

    # def send_to_hod(self):
    #     email_from = self.env.user.email
    #     mail_to = self.employee_id.work_email
    #     group_user_id = self.env.ref('ikoyi_module.ikoyi_hod').id
    #     self.mail_sending(email_from, group_user_id, mail_to)
    #     self.write({'state': 'hod'})

    def send_to_hr_manager_three(self):
        self.check_fields()
        email_from = self.env.user.email
        mail_to = self.employee_id.work_email
        group_user_id = self.env.ref('hr.group_hr_manager').id
        self.mail_sending(email_from, group_user_id, mail_to)
        self.write({'state': 'hr_manager_three'})

    def print_appraisal(self):
        pass

    def cancel_button(self):
        self.write({'state': 'draft'})
 
    def refuse_button(self):
        self.write({'state': 'refuse'})
 
    def send_mail_to_one(self, email_from, mail_to):
        from_browse = self.env.user.name
        for order in self:
            email_froms = str(from_browse) + " <"+str(email_from)+">"
            subject = "Appraisal"
            bodyx = "Dear Sir/Madam, </br>We wish to notify you that appraisal form for a memo request from {} has been approved. </br> </br>Kindly review it. </br> </br>Thanks".format(self.employee_id.name)
            mail_data = {
                        'email_from': email_froms,
                        'subject':subject,
                        'email_to': mail_to,
                        # 'email_cc':mail_appends,
                        'reply_to': email_from,
                        'body_html':bodyx
                        }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)

    def mail_sending(self, email_from, group_user_id, extra):
        from_browse = self.env.user.name
        groups = self.env['res.groups']

        for order in self:
            group_users = groups.search([('id','=', group_user_id)])
            group_emails = group_users.users
            append_mails = []
            email_to = []
            # for group_mail in self.users_followers:
            #     append_mails.append(group_mail.work_email)
            for gec in group_emails:
                email_to.append(gec.login)
            email_froms = str(from_browse) + " <"+str(email_from)+">"
            # mail_appends = (', '.join(str(item)for item in append_mails))
            subject = "Appraisal"
            bodyx = "Dear Sir/Madam, </br>We wish to notify you that an appraisal form for {} has been sent to you for approval </br> </br>Kindly review it. </br> </br>Thanks".format(self.employee_id.name)
            extrax = (', '.join(str(extra)))
            append_mails.append(extrax)
            mail_data = {
                        'email_from': email_froms,
                        'subject':subject,
                        'email_to':email_to,
                        # 'email_cc':mail_appends,
                        'reply_to': email_from,
                        'body_html':bodyx
                        }
            mail_id = order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)
