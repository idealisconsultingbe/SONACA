import pdfplumber
import string
import re
import docx2txt
import pytesseract
import nltk

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from langdetect import detect
from googletrans import Translator
from pdf2image import convert_from_path

nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')


def text_processing(txt):
    # Convert all strings to lowercase
    txt = txt.lower()
    # Remove numbers
    txt = re.sub(r'\d+', '', txt)
    # Remove punctuation
    txt = txt.translate(str.maketrans('', '', string.punctuation))
    # Remove special character
    txt = re.sub(r'\W+', ' ', txt)
    if txt:
        language = detect(txt)
        # print("language: ",language)
        # print("text before translation:", txt)
        if language != 'en':
            translator = Translator()
            result = translator.translate(txt, src=language, dest='en')
            txt = result.text
    # print('text after translation: ',txt)
    # Remove stopwords + lemmatizer
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(txt)
    filtered_sentence = [w for w in word_tokens if w not in stop_words]
    sentence = ''
    for w in filtered_sentence:
        # lemming
        w = lemmatizer.lemmatize(w)
        if len(w) > 1:
            sentence += w + ' '
    txt = sentence
    # print("text after processing", txt)
    return txt


def get_jaccard_sim(str1, str2):
    # length of intersection divided length text CV
    a = set(str1.split())
    b = set(str2.split())
    c = a.intersection(b)
    return float(len(c)) / len(b)


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


def job_description_processing(job_description_html):
    job_description_txt = re.sub('<[^<]+>', "", job_description_html)
    job_description_txt = re.sub(r'[^ \nA-Za-z0-9À-ÖØ-öø-ÿЀ-ӿ/]+', ' ', job_description_txt)
    job_description_txt = ' '.join(job_description_txt.split())
    return job_description_txt


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
