# ############################################
# {Description}
# Download pdf by link, convert it to text, split into paragraphs.
# ############################################

from io import StringIO
import os
import wget
import pandas as pd

from sch_search.weaviate.weaviate_calls import import_data

#pdf miner imports
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser


FS_DIR = os.path.dirname(os.path.realpath(__file__)) + '/pdfs/'

def clear_fs():
    filelist = [f for f in os.listdir(FS_DIR)]
    for f in filelist:
        os.remove(os.path.join(FS_DIR, f))

def download(link, filename):
    ''' Download a file to scholarhub-search/parsers/pdfs/<filename>
        link: URL where the file can be found
        filename: What you want the downloaded file to be called
        Returns path of the file once it is downloaded.
    '''
    path = FS_DIR + filename
    if os.path.exists(path):
        os.remove(path)
    wget.download(link, path)
    return path

def paragraph_splitting_heuristic(paragraphs):
    ''' Splits the paragraphs at double newlines but then takes steps to combine shorter paragraphs with adjacent paragraphs
    paragraphs: List of strings where each string is a naively-determined paragraph
    returns: List of strings where each string is a paragraph which may have been heuristically combined with adjacent paragraphs
    '''
    newparagraphs=[]
    i=1
    for block in paragraphs:
        block=block.replace("\n", " ")
        if (len(newparagraphs)==0):
            newparagraphs.append(block)
        elif (len(newparagraphs[-1])<200):
            newparagraphs[-1]=newparagraphs[-1]+' '+block
        else:
            newparagraphs.append(block)

    if (len(newparagraphs) > 1 and len(newparagraphs[-1])<100):
        newparagraphs[-2]=newparagraphs[-2]+' '+newparagraphs[-1]
        newparagraphs.pop()
    return newparagraphs

def pdf2pages(pdf_path):
    '''
    Converts a pdf file to pages of text using pdfminer library.
    pdf_path: Path to the downloaded pdf file, relative to scholarhub-search directory
    Returns a list of strings where each string represents the text of an entire page.
    '''
    pages = []
    with open(pdf_path, 'rb') as in_file: #open the pdf
        parser = PDFParser(in_file) #parse it
        doc = PDFDocument(parser) #create a document
        #for each page extract the text and append it to the pages
        page_number=0
        for page in PDFPage.create_pages(doc):
            text = StringIO()
            r = PDFResourceManager()
            d = TextConverter(r, text, laparams=LAParams())
            interpreter = PDFPageInterpreter(r, d)
            interpreter.process_page(page)
            text=text.getvalue().replace("\ufb01", "fi")
            pages.append(text)
    return pages

def pages2dataframe(pages, title, paragraph_splitting='naive'):
    ''' Converts text from pdf to dataframe, breaking it into paragraphs
        pages: list of strings where each string is a page of the pdf
        title: How to uniquely identify the pdf in the database
            (usually the link to the pdf online)
        paragraph_splitting: How to split the pdf into paragraphs; current options are
            "naive" (split at double newlines) and "heuristic" (in paragraph_splitting_heuristic) and "none"
        Returns dataframe with columns Document, Page, Paragraph, Text and each row is a paragraph
    '''

    df = pd.DataFrame(columns = ['Text', 'Document', 'Page', 'Paragraph','Type'])
    for p in range(len(pages)):
        text = pages[p]
        if paragraph_splitting == 'none':
            paragraphs = [text]
        else:
            # Naive paragraph splitting: split at newlines
            paragraphs=text.split('\n\n')
            if paragraph_splitting == 'heuristic':
                paragraphs = paragraph_splitting_heuristic(paragraphs)
        # 1-index the paragraphs
        paragraph_number=1
        for block in paragraphs:
            block=block.replace("\n", " ")
            # 1-index the pages
            page_number = p + 1
            df = df.append({'Text' : block, 'Document' : title, 'Page' : page_number, 'Paragraph' : paragraph_number}, ignore_index = True)
            paragraph_number=paragraph_number+1
    return df #return the list of string for each paged


def parse_pdf(client, links, paragraph_splitting='naive'):
    ''' Take in a list of links to pdfs, parse them into blocks of text, and add them to Weaviate.
    links: list of web links, each of which should be a pdf
    paragraph_splitting: can be 'naive' (split by double newline) or 'heuristic'
        (split by double newline and then recombine shorter paragraphs with the ones after them) or 'none' (don't split the page up by paragraphs at all)
    returns: None
    '''
    for link in links:
        path = download(link, "tempDownload.pdf")
        pages = pdf2pages(path)
        df = pages2dataframe(pages, link, paragraph_splitting) #list of pages with lists of paragraphs inside
        import_data(client, df)



#testing only
# from sch_search.weaviate.weaviate_calls_dev import connect
# parse_pdf(connect(), ["https://www.sp18.eecs70.org/static/notes/n0.pdf"], paragraph_splitting='heuristic')
