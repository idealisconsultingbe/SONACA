import pdfplumber
import re
import string
import docx2txt
import pytesseract
from pdf2image import convert_from_path
from pyresparser import ResumeParser


def text_processing(txt):
    # Convert all strings to lowercase
    txt = txt.lower()
    # Remove numbers
    txt = re.sub(r'\d+', '', txt)
    # Remove punctuation
    txt = txt.translate(str.maketrans('', '', string.punctuation))
    # Remove special character
    txt = re.sub(r'\W+', ' ', txt)

    return txt


def cv_parser(filename, text_cv):
    try:
        parser_cv = ResumeParser(filename).get_extracted_data()
    except Exception:
        parser_cv = {'mobile_number': '', 'email': '', 'name': ''}

    # Find the correct phone number
    phones = re.findall(r'[-\d\+\(\)\s\.\/]{9,25}', text_cv)
    list_phone_numbers = []
    for phone in phones:
        num = (
            phone.replace('-', '')
            .replace(' ', '')
            .replace('/', '')
            .replace('.', '')
            .replace(')', '')
            .replace('(', '')
            .replace('\n', '')
        )
        num = ''.join(num.split())

        if len(num) == 9:
            if num[0] == '0':
                list_phone_numbers.append(num)
        if len(num) == 10:
            if num[0] == '0':
                list_phone_numbers.append(num)
        if 12 <= len(num) <= 13:
            if num[0] == '+':
                list_phone_numbers.append(num)
        if 13 <= len(num) <= 14:
            if num[0] == '0' and num[1] == '0':
                list_phone_numbers.append(num)
    parser_cv["mobile_number"] = list(set(list_phone_numbers))

    # add email
    emails = re.findall(r'[\w\.-]+@[\w\.-]+', text_cv)
    if parser_cv["email"]:
        emails.append(parser_cv["email"])
    parser_cv["email"] = list(set(emails))

    # remove numbers from name
    if parser_cv['name']:
        name = re.sub(r'\d+', '', parser_cv["name"])
        # Remove special character
        parser_cv["name"] = re.sub(r'\W+', ' ', name)

    return parser_cv


def pdf_to_txt(cv_pdf):
    text_cv = ''
    with pdfplumber.open(cv_pdf) as pdf:
        pages = pdf.pages
        for idx, page in enumerate(pages):
            txt_page = page.extract_text(x_tolerance=1, y_tolerance=1)
            if txt_page:
                text_cv += txt_page
    return text_cv


def docx_to_text(cv_docx):
    text = docx2txt.process(cv_docx)
    return text


def binary_to_hex(cv_binary):
    out_hex = ['{:02X}'.format(b) for b in cv_binary]
    return out_hex


def image_to_text(filename, tesseract_path):
    path = tesseract_path
    pytesseract.pytesseract.tesseract_cmd = path
    text = pytesseract.image_to_string(filename)
    return text


def pdf_to_image(filename, poppler_path):
    path = poppler_path
    images = convert_from_path(filename, poppler_path=path)
    return images
