import base64
import io
import logging

from .encoding_functions import (
    text_processing,
    cv_parser,
    pdf_to_txt,
    docx_to_text,
    binary_to_hex,
    image_to_text,
    pdf_to_image,
)

from odoo import models

_logger = logging.getLogger(__name__)


class Applicant(models.Model):
    _inherit = "hr.applicant"

    # main function called with button in Odoo recruitment ("encode info")
    def encode_applicant(self):

        # find in system parameters the tesseract and poppler files (see readme for more info)
        tesseract_path = (
            self.env['ir.config_parameter'].sudo().get_param('hr_recruitment_encoding.tesseract_path') or ''
        )
        poppler_path = self.env['ir.config_parameter'].sudo().get_param('hr_recruitment_encoding.poppler_path') or ''

        # iterate through applicants
        for record in self:

            parser_cv = {}

            if not record.attachment_ids:
                _logger.info("No attachments")
                continue

            if len(record.attachment_ids) == 1:

                cv_binary = base64.b64decode(record.attachment_ids.datas)

                # check if the attachment is a PDF file
                if len(cv_binary) > 20 and '%PDF' in str(cv_binary[0:20]):
                    f = open('file.pdf', 'wb')
                    f.write(cv_binary)
                    f.close()
                    cv_pdf = io.BytesIO(cv_binary)
                    text_cv = pdf_to_txt(cv_pdf)

                    # check if the attachment is not a scan or an image
                    if len(text_cv) < 50:
                        images = pdf_to_image('file.pdf', poppler_path)
                        for image in images:
                            text_cv += image_to_text(image, tesseract_path)
                    parser_cv = cv_parser('file.pdf', text_cv)

                # check if the attachment is a docx file
                elif binary_to_hex(cv_binary)[0:4] == ['50', '4B', '03', '04']:
                    f = open('file.docx', 'wb')
                    f.write(cv_binary)
                    f.close()
                    text_cv = docx_to_text('file.docx')

                    # cv parser (search name, mail, phone and returns a dictionary)
                    parser_cv = cv_parser('file.docx', text_cv)

                else:
                    _logger.info("Not supported format")
                    continue

                if parser_cv:
                    if 'name' in parser_cv:
                        if parser_cv['name'] and not record.partner_name:
                            record.partner_name = parser_cv['name']

                    if 'mobile_number' in parser_cv:
                        if parser_cv['mobile_number'] and not record.partner_mobile:
                            record.partner_mobile = parser_cv['mobile_number'][0]
                        if parser_cv['mobile_number'] and not record.partner_phone:
                            if len(parser_cv['mobile_number']) > 1:
                                record.partner_phone = parser_cv['mobile_number'][1]

                    if 'email' in parser_cv:
                        if parser_cv['email'] and not record.email_from:
                            record.email_from = parser_cv['email'][0]
                        if parser_cv['email'] and not record.email_cc:
                            if len(parser_cv['email']) > 1:
                                record.email_cc = parser_cv['email'][1]

                if text_cv:
                    text_cv = text_processing(text_cv)
                    words_cv = text_cv.split()

                    # find the university degree
                    words_bachelor = ['bachelier', 'bachelor', 'bachelors', 'baccalauréat']
                    words_master = ['master', 'masters']
                    words_phd = ['doctorat', 'phd']
                    degrees = self.env['hr.recruitment.degree'].search([])
                    best_degree_idx = 0

                    # find the existing tags
                    tags = self.env['hr.applicant.category'].search([]) or []
                    list_tags = [text_processing(x.name) for x in tags]

                    for word in words_cv:
                        if word in words_phd:
                            best_degree_idx = 3
                        elif word in words_master:
                            best_degree_idx = max(best_degree_idx, 2)
                        elif word in words_bachelor:
                            best_degree_idx = max(best_degree_idx, 1)
                        else:
                            best_degree_idx = max(best_degree_idx, 0)
                        if word in list_tags:
                            idx = list_tags.index(word)
                            record.categ_ids += tags[idx]
                    record.type_id = degrees[best_degree_idx]

            else:
                _logger.info("More than one attachment found")
                continue
