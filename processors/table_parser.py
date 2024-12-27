"""
Parses csv data in order to put into weaviate
"""
import pandas as pd
from core.weaviate import import_data

def get_paragraphs(csv):
    """
    Gets the paragraphs from the csv data file
    """
    d_f = pd.read_csv(csv)
    d_f = d_f.dropna()
    return d_f

def parse_csv(client, csvs):
    """
    Parses the csv
    """
    for csv in csvs:
        d_f = get_paragraphs(csv)
        import_data(client, d_f)
