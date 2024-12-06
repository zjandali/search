# ############################################
# {Description}
# Download a PDF by link, convert it to text, and split it into paragraphs.
# ############################################

from io import StringIO
import os
import wget
import pandas as pd

from sch_search.weaviate.weaviate_calls import import_data

# PDFMiner imports
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

FS_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pdfs/')


def clear_fs():
    """Clears all files in the PDF storage directory."""
    filelist = [f for f in os.listdir(FS_DIR)]
    for f in filelist:
        os.remove(os.path.join(FS_DIR, f))


def download(link, filename):
    """
    Downloads a file to the specified directory.

    Args:
        link: URL of the file to be downloaded.
        filename: Name for the downloaded file.

    Returns:
        The file path of the downloaded file.
    """
    path = os.path.join(FS_DIR, filename)
    if os.path.exists(path):
        os.remove(path)
    wget.download(link, path)
    return path


def paragraph_splitting_heuristic(paragraphs):
    """
    Splits paragraphs at double newlines and combines shorter paragraphs with adjacent ones.

    Args:
        paragraphs: List of strings representing naively split paragraphs.

    Returns:
        A refined list of paragraphs, combining shorter ones when appropriate.
    """
    new_paragraphs = []
    for block in paragraphs:
        block = block.replace("\n", " ")
        if not new_paragraphs or len(new_paragraphs[-1]) >= 200:
            new_paragraphs.append(block)
        else:
            new_paragraphs[-1] += ' ' + block

    if len(new_paragraphs) > 1 and len(new_paragraphs[-1]) < 100:
        new_paragraphs[-2] += ' ' + new_paragraphs[-1]
        new_paragraphs.pop()

    return new_paragraphs


def pdf2pages(pdf_path):
    """
    Converts a PDF file to pages of text using the PDFMiner library.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        A list of strings where each string is the text content of a page.
    """
    pages = []
    with open(pdf_path, 'rb') as in_file:
        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        for page in PDFPage.create_pages(doc):
            text = StringIO()
            resource_manager = PDFResourceManager()
            converter = TextConverter(resource_manager, text, laparams=LAParams())
            interpreter = PDFPageInterpreter(resource_manager, converter)
            interpreter.process_page(page)
            pages.append(text.getvalue().replace("\ufb01", "fi"))  # Replace ligature for 'fi'
    return pages


def pages2dataframe(pages, title, paragraph_splitting='naive'):
    """
    Converts text from a PDF into a DataFrame, splitting it into paragraphs.

    Args:
        pages: List of strings where each string is a page of the PDF.
        title: Unique identifier for the PDF in the database (e.g., link to the PDF online).
        paragraph_splitting: Method for splitting paragraphs ('naive', 'heuristic', or 'none').

    Returns:
        A pandas DataFrame with columns: Document, Page, Paragraph, and Text.
    """
    df = pd.DataFrame(columns=['Text', 'Document', 'Page', 'Paragraph', 'Type'])
    for page_number, text in enumerate(pages, start=1):
        if paragraph_splitting == 'none':
            paragraphs = [text]
        else:
            paragraphs = text.split('\n\n')
            if paragraph_splitting == 'heuristic':
                paragraphs = paragraph_splitting_heuristic(paragraphs)

        for paragraph_number, block in enumerate(paragraphs, start=1):
            block = block.replace("\n", " ")
            df = df.append({
                'Text': block,
                'Document': title,
                'Page': page_number,
                'Paragraph': paragraph_number
            }, ignore_index=True)
    return df


def parse_pdf(client, links, paragraph_splitting='naive'):
    """
    Parses a list of PDF links into blocks of text and uploads them to Weaviate.

    Args:
        client: Weaviate client instance for database operations.
        links: List of URLs to PDFs.
        paragraph_splitting: Method for splitting paragraphs ('naive', 'heuristic', or 'none').

    Returns:
        None.
    """
    for link in links:
        path = download(link, "tempDownload.pdf")
        pages = pdf2pages(path)
        df = pages2dataframe(pages, link, paragraph_splitting)
        import_data(client, df)


# Uncomment the lines below for testing purposes only
# from sch_search.weaviate.weaviate_calls_dev import connect
# parse_pdf(connect(), ["https://www.sp18.eecs70.org/static/notes/n0.pdf"], paragraph_splitting='heuristic')
