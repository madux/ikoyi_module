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


class HrContract(models.Model):
    _inherit = ['hr.contract']
    
    type_structure = fields.Selection([('salary', 'Organization Salary'),
                              ('leave', 'Leave Bonus Structure'),
                              ('contribution', 'Contribution')],
                             string='Type of Structure', index=True,
                             copy=True, default='salary',
                             track_visibility='onchange')