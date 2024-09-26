import unittest
from sch_search.commands import add_resource, del_resource
from sch_search.weaviate.weaviate_calls_dev import connect
from sch_search.weaviate.weaviate_calls import import_data
from sch_search.parsers.pdf_parser import paragraph_splitting_heuristic, pdf2pages, download
import pandas as pd


class MyTestCase(unittest.TestCase):
    client = connect()
    #Resources that are meant to cointunously be added and deleted by this script for testing purposes
    io_resources = ['http://www.sp18.eecs70.org/static/notes/n1.pdf', 'http://www.sp18.eecs70.org/static/notes/n2.pdf']
    #Resources that are meant to remain in weaviate at all times for testing purposes
    resources = ['http://www.sp18.eecs70.org/static/notes/n4.pdf', 'http://www.sp18.eecs70.org/static/notes/n3.pdf']

    blank_pdf = download('https://mag.wcoomd.org/uploads/2018/05/blank.pdf', 'tempDownload.pdf')
    csv = 'tests/data/data.csv'


    def test_del_resource(self):
        #First adds resources that are to be deleted
        add_resource.add_resources(self.client, self.io_resources + self.resources)
        #Run function being tested
        del_resource.delete_link_data(self.client, self.io_resources)
        #Iterate over all io_resources and query weaviate for them to ensure that nothing is returned
        for link in self.io_resources:
            where_filter = {
                "path": ["document"],
                "operator": "Equal",
                "valueText": link
            }
            data = self.client.query.get("Post", ["document", "_additional {id}"]). \
                with_where(where_filter).do()
            self.assertEqual(len(data['data']['Get']['Post']), 0)
        #Makes sure that no resources were accidently deleted
        for link in self.resources:
            where_filter = {
                "path": ["document"],
                "operator": "Equal",
                "valueText": link
            }
            data = self.client.query.get("Post", ["document", "_additional {id}"]). \
                with_where(where_filter).do()
            self.assertNotEqual(len(data['data']['Get']['Post']), 0)
        add_resource.add_resources(self.client, self.io_resources)

    def test_add_resource(self):
        #First delete resources that are to be added
        del_resource.delete_link_data(self.client, self.resources)
        #Run function being tested
        add_resource.add_resources(self.client, self.resources)
        for link in self.resources:
            where_filter = {
                "path": ["document"],
                "operator": "Equal",
                "valueText": link
            }
            data = self.client.query.get("Post", ["document", "_additional {id}"]). \
                with_where(where_filter).do()
            self.assertNotEqual(len(data['data']['Get']['Post']), 0)






    def test_import_data(self):
        d_f = pd.read_csv(self.csv)
        import_data(self.client, d_f)
        for row in d_f.iterrows():
            #makes sure the data was imported
            where_filter = {
                "path": ["document"],
                "operator": "Equal",
                "ValueText": row["Document"]
            }
            data = self.client.query.get("Post", ["document", "_additional {id}"]). \
                with_where(where_filter).do()
            self.assertNotEqual(len(data['data']['Get']['Post']), 0)


    def test_pdf_parser(self):
        text = pdf2pages(self.blank_pdf)
        paragraphs = paragraph_splitting_heuristic(len)
        self.assertEqual(len(text), 0)
        self.assertEqual(len(paragraphs), 0)
















if __name__ == '__main__':
    unittest.main()


