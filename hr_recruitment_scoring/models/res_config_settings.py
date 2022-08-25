from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tesseract_path = fields.Char(
        string="Path to tesseract exe", config_parameter='hr_recruitment_scoring.tesseract_path'
    )
    poppler_path = fields.Char(string="Path to poppler exe", config_parameter='hr_recruitment_scoring.poppler_path')
