'''
Created on May 1, 2012

@author: quandtan
'''
import unittest
from applicake.framework.logger import Logger
from applicake.applications.proteomics.openms.filehandling.fileconverter import Mzxml2MzmlTemplate 
from StringIO import StringIO


class Test(unittest.TestCase):


    def setUp(self):
        log_stream = StringIO()
        self.log = Logger.create(level='DEBUG',name='memory_logger',stream=log_stream)
        self.mzxml = 'my.mzXML'
        self.mzml = 'my.mzML'        

    def test_mzxml2mzml_template(self):
        tpl = Mzxml2MzmlTemplate()
        info = {tpl.mzml_key: self.mzml,
                tpl.mzxml_key: self.mzxml}
        template, info = tpl.read_template(info, self.log)
        assert '$MZXML' in template
        assert '$MZML' in template
        mod_template,info = tpl.replace_vars(info, self.log, template)
        assert self.mzml in mod_template
        assert self.mzxml in mod_template
        assert '$' not in mod_template


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()