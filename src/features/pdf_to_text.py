import os
import pdfplumber
from tqdm import tqdm
import pytesseract
import fitz
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

import os
from tqdm import tqdm

def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)

def convert_pdf2txt(src_dir, dest_dir):
    files = os.listdir(src_dir)
    files = [i for i in files if '.pdf' in i]
    groups = {}
    for file in files:
        base_name = file.replace('.pdf', '').split(' (')[0]
        if base_name in groups:
            groups[base_name].append(file)
        else:
            groups[base_name] = [file]

    for base_name, group in tqdm(groups.items()):
            text = ''
            for file in group:
                try:
                    doc = fitz.open(src_dir + file)
                    curr_text = ''
                    for page in doc:
                        curr_text += page.get_text("text")
                    if len(curr_text) < 100:
                        raise Exception(f'Not enough text for {file}')
                    text += curr_text

                except Exception as e:
                    try:
                        with pdfplumber.open(src_dir + file) as pdf:
                            for page in pdf.pages:
                                image = page.to_image()
                                image.save("temp.png")
                                pil_image = Image.open("temp.png")
                                text += pytesseract.image_to_string(pil_image, lang='dan')
                        print(f'Using OCR for {file}')
                    except Exception as e:
                        print(f'Error processing {file}: {e}')
                        continue
            save_file(dest_dir + base_name + '.txt', text.strip())


if __name__ == '__main__':
    #convert_docx2txt('docx/', 'converted/')
    convert_pdf2txt('data/pdfs/', 'data/processed/')