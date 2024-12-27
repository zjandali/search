"""
PDF Parsing Module
This module handles downloading PDFs, converting them to text,
splitting into paragraphs, and uploading the extracted data to Weaviate.
"""
import os
import wget
import pandas as pd
from io import StringIO
from weaviate.weaviate_calls import import_data

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

PDF_STORAGE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pdfs/')

def clear_pdf_storage():
    """Removes all files from the PDF storage directory."""
    for filename in os.listdir(PDF_STORAGE_DIR):
        file_path = os.path.join(PDF_STORAGE_DIR, filename)
        os.remove(file_path)

def download_pdf(url, filename):
    """
    Downloads a PDF from the given URL to the specified filename.
    
    Args:
        url (str): URL of the PDF to download.
        filename (str): Desired filename for the downloaded PDF.
    
    Returns:
        str: Path to the downloaded PDF file.
    """
    file_path = os.path.join(PDF_STORAGE_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    wget.download(url, file_path)
    return file_path

def split_paragraphs_heuristic(paragraph_list):
    """
    Processes a list of paragraphs, merging shorter ones with preceding paragraphs.
    
    Args:
        paragraph_list (list): List of paragraph strings.
    
    Returns:
        list: Refined list of paragraphs.
    """
    refined = []
    for paragraph in paragraph_list:
        paragraph = paragraph.replace("\n", " ")
        if not refined or len(refined[-1]) >= 200:
            refined.append(paragraph)
        else:
            refined[-1] += ' ' + paragraph

    if len(refined) > 1 and len(refined[-1]) < 100:
        refined[-2] += ' ' + refined.pop()
    
    return refined

def convert_pdf_to_text(pdf_path):
    """
    Converts a PDF file to a list of text pages using PDFMiner.
    
    Args:
        pdf_path (str): Path to the PDF file.
    
    Returns:
        list: List containing text of each page.
    """
    pages_text = []
    with open(pdf_path, 'rb') as file:
        parser = PDFParser(file)
        document = PDFDocument(parser)
        for page in PDFPage.create_pages(document):
            text_stream = StringIO()
            resource_manager = PDFResourceManager()
            converter = TextConverter(resource_manager, text_stream, laparams=LAParams())
            interpreter = PDFPageInterpreter(resource_manager, converter)
            interpreter.process_page(page)
            pages_text.append(text_stream.getvalue().replace("\ufb01", "fi"))
    return pages_text

def pages_to_dataframe(pages, document_title, splitting='naive'):
    """
    Converts PDF pages into a structured DataFrame.
    
    Args:
        pages (list): List of page texts.
        document_title (str): Identifier for the document.
        splitting (str): Method to split paragraphs ('naive', 'heuristic', or 'none').
    
    Returns:
        pd.DataFrame: DataFrame with structured text data.
    """
    df = pd.DataFrame(columns=['Text', 'Document', 'Page', 'Paragraph', 'Type'])
    for page_num, text in enumerate(pages, start=1):
        if splitting == 'none':
            paragraphs = [text]
        else:
            paragraphs = text.split('\n\n')
            if splitting == 'heuristic':
                paragraphs = split_paragraphs_heuristic(paragraphs)
        
        for para_num, paragraph in enumerate(paragraphs, start=1):
            paragraph = paragraph.replace("\n", " ")
            df = df.append({
                'Text': paragraph,
                'Document': document_title,
                'Page': page_num,
                'Paragraph': para_num
            }, ignore_index=True)
    return df

def process_pdf(client, urls, splitting_method='naive'):
    """
    Downloads, parses, and uploads PDF data to Weaviate.
    
    Args:
        client: Weaviate client instance.
        urls (list): List of PDF URLs.
        splitting_method (str): Method for splitting paragraphs.
    
    Returns:
        None
    """
    for url in urls:
        downloaded_path = download_pdf(url, "tempDownload.pdf")
        pages = convert_pdf_to_text(downloaded_path)
        dataframe = pages_to_dataframe(pages, url, splitting_method)
        import_data(client, dataframe)


