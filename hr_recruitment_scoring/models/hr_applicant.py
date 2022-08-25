import base64
import io
import re
import logging
import random

from .cv_scoring_functions import (
    text_processing,
    get_jaccard_sim,
    pdf_to_txt,
    docx_to_text,
    job_description_processing,
    binary_to_hex,
    image_to_text,
    pdf_to_image,
)

from odoo import fields, models

_logger = logging.getLogger(__name__)


class Applicant(models.Model):
    _inherit = "hr.applicant"

    score = fields.Float(string="Score", readonly=False)
    score_jaccard = fields.Float(string="Score Text Matching", readonly=False)
    score_keywords = fields.Float(string="Score Keywords Matching", readonly=False)

    # main function called with button in Odoo recruitment ("compute score")
    def process_applicant(self):

        # find in system parameters the tesseract and poppler files (see readme for more info)
        tesseract_path = ''
        poppler_path = ''
        if self.env['ir.config_parameter'].sudo().get_param('hr_recruitment_scoring.tesseract_path'):
            tesseract_path = self.env['ir.config_parameter'].sudo().get_param('hr_recruitment_scoring.tesseract_path')
        if self.env['ir.config_parameter'].sudo().get_param('hr_recruitment_scoring.poppler_path'):
            poppler_path = self.env['ir.config_parameter'].sudo().get_param('hr_recruitment_scoring.poppler_path')

        job_txt = ''
        bool_job_description = True

        length_job_description = 0
        tags = []

        scores = []
        jaccard_scores = []
        keywords_scores = []

        # iterate through applicants
        for record in self:
            score_attachment = []
            scores_jaccard_attachment = []
            scores_keywords_attachment = []
            if not record.attachment_ids:
                _logger.info("No attachments")
                continue

            # loop through the attachments (and keep the relevant one)
            for attachment in record.attachment_ids:
                score = 0
                cv_text = ''

                cv_binary = base64.b64decode(attachment.datas)

                # check if the attachment is a PDF file
                if len(cv_binary) > 5 and '%PDF' in str(cv_binary[0:20]):
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

                # check if the attachment is a docx file
                elif binary_to_hex(cv_binary)[0:4] == ['50', '4B', '03', '04']:
                    f = open('file.docx', 'wb')
                    f.write(cv_binary)
                    f.close()
                    text_cv = docx_to_text('file.docx')

                else:
                    _logger.info("Not supported format")
                    continue

                # check if text is found in the attachment
                if text_cv:
                    cv_text = text_processing(text_cv)
                else:
                    _logger.info("No text found in CV")
                    continue

                # find job description on website and process it
                if bool_job_description and record.job_id.website_description:
                    job_description_html = record.job_id.website_description
                    tags = re.findall(r'[#]\w+', job_description_html)
                    tags = [text_processing(word) for word in tags]
                    job_description_txt = job_description_processing(job_description_html)
                    job_txt = text_processing(job_description_txt)
                    length_job_description = len(job_txt.split())
                    bool_job_description = False

                # find keywords in job description on website with "#" and process it
                keywords_txt = ''
                if record.job_id.name:
                    keywords_txt = text_processing(record.job_id.name)
                keywords_processed = keywords_txt.split()
                words_cv = cv_text.split()
                for word in tags:
                    if word:
                        keywords_processed.append(word.strip())
                # set or list (words in duplicates or not)
                # words_cv_without_duplicates = set(words_cv)
                for word in keywords_processed:
                    if word in words_cv:
                        _logger.info("Keyword: ")
                        _logger.info(word)
                        score += 1
                _logger.info("Score keywords: ")
                _logger.info(score)

                scores_keywords_attachment.append(score)

                # compute jaccard score (similarity between text of CV and text of job description)
                jac = round(get_jaccard_sim(job_txt, cv_text), 3) * (length_job_description / 10)
                _logger.info("Score Jaccard: ")
                _logger.info(jac)
                scores_jaccard_attachment.append(jac)
                score += jac
                score += (random.random() * random.randint(4, 20))

                # set the score of the applicant
                score_attachment.append(score)
                _logger.info("Total score: ")
                _logger.info(score)

            # set the scores
            if score_attachment:
                index_best_attachment = score_attachment.index(max(score_attachment))
                # score keywords
                keywords_scores.append(scores_keywords_attachment[index_best_attachment])
                record.score_keywords = scores_keywords_attachment[index_best_attachment]
                # score jaccard (cv matching)
                jaccard_scores.append(scores_jaccard_attachment[index_best_attachment])
                record.score_jaccard = scores_jaccard_attachment[index_best_attachment]
                # global scores
                scores.append(score_attachment[index_best_attachment])
                record.score = score_attachment[index_best_attachment]
