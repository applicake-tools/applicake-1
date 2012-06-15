'''
Created on May 27, 2012

@author: quandtan
'''
import os
from applicake.framework.interfaces import IWrapper
from applicake.applications.proteomics.modifications import ModificationDb
from applicake.applications.proteomics.enzymes import EnzymeDb

class MsMsIdentification(IWrapper):
    '''
    Basic wrapper class for search engines in MS/MS analysis
    '''
    
    STATIC_MODS = 'STATIC_MODS'
    VARIABLE_MODS = 'VARIABLE_MODS'

    _template_file = ''
    _result_file = ''
    _default_prefix = ''   
    
    def __init__(self):
        """
        Constructor
        """
        base = self.__class__.__name__
        self._template_file = '%s.tpl' % base # application specific config file
        self._result_file = '%s.result' % base # result produced by the application    

    def define_enzyme(self,info,log):
        """
        Convert generic enzyme into the program-specific format
        """
        converted_enzyme = EnzymeDb(log).get(info['Enzyme'], self.__class__.__name__)
        info['Enzyme'] = converted_enzyme                
        return info 
    
    def define_mods(self,info,log):
        """
        Convert generic static/variable modifications into the program-specific format 
        """
        mod_keys = [self.STATIC_MODS,self.VARIABLE_MODS]
        for key in mod_keys:
            if not info.has_key(key):
                info[key] = ''
            else:
                mods = []
                for mod in info[key].split(';'):
                    log.debug('modification [%s]' % key)
                    log.debug('name [%s]')
                    converted_mod = ModificationDb(log).get(mod, self.__class__.__name__)
                    mods.append(converted_mod)
                info[key] = ','.join(mods)                
        return info 
    
    
        
    def get_prefix(self,info,log):
        if not info.has_key(self.PREFIX):
            info[self.PREFIX] = self._default_prefix
            log.debug('set [%s] to [%s] because it was not set before.' % (self.PREFIX,info[self.PREFIX]))
        return info[self.PREFIX],info             

    def set_args(self,log,args_handler):
        """
        See super class.
        
        Set several arguments shared by the different search engines
        """        
        args_handler.add_app_args(log, self.PREFIX, 'Path to the OpenMS executable')
        args_handler.add_app_args(log, self.TEMPLATE, 'Path to the template file')
        args_handler.add_app_args(log, 'FRAGMASSERR', 'Fragment mass error')
        args_handler.add_app_args(log, 'FRAGMASSUNIT', 'Unit of the fragment mass error')
        args_handler.add_app_args(log, 'PRECMASSERR', 'Precursor mass error')
        args_handler.add_app_args(log, 'PRECMASSUNIT', 'Unit of the precursor mass error')
        args_handler.add_app_args(log, 'MISSEDCLEAVAGE', 'Number of maximal allowed missed cleavages')
        args_handler.add_app_args(log, 'DBASE', 'Sequence database file with target/decoy entries')
        args_handler.add_app_args(log, 'ENZYME', 'Enzyme used to digest the proteins')
        args_handler.add_app_args(log, self.STATIC_MODS, 'List of static modifications')
        args_handler.add_app_args(log, self.VARIABLE_MODS, 'List of variable modifications')
        args_handler.add_app_args(log, 'THREADS', 'Number of threads used in the process.')
        args_handler.add_app_args(log, self.WORKDIR, 'Directory to store files')  
        args_handler.add_app_args(log, self.COPY_TO_WD, 'List of files to store in the work directory')   
        return args_handler
    
    def validate_run(self,info,log, run_code,out_stream, err_stream):
        """
        See super class.
        
        Return the unaltered run_code from the tool execution as exit_code.
        """  
        if 0 != run_code:
            return run_code,info
        return 0,info 
 
class OpenMs(IWrapper):
    '''
    Basic wrapper class for OpenMS tools
    '''
    
    _template_file = ''
    _result_file = ''
    _default_prefix = ''   
    
    def __init__(self):
        """
        Constructor
        """
        base = self.__class__.__name__
        self._template_file = '%s.ini' % base # application specific config file    
    
    def get_prefix(self,info,log):
        if not info.has_key(self.PREFIX):
            info[self.PREFIX] = self._default_prefix
            log.debug('set [%s] to [%s] because it was not set before.' % (self.PREFIX,info[self.PREFIX]))
        return info[self.PREFIX],info     

    def set_args(self,log,args_handler):
        """
        See super class.
        
        Set several arguments shared by the different search engines
        """        
        args_handler.add_app_args(log, self.PREFIX, 'Path to the OpenMS executable')
        args_handler.add_app_args(log, self.TEMPLATE, 'Path to the openMS-template file')
        args_handler.add_app_args(log, 'THREADS', 'Number of threads used in the process.')
        args_handler.add_app_args(log, self.WORKDIR, 'Directory to store files')  
        args_handler.add_app_args(log, self.COPY_TO_WD, 'List of files to store in the work directory')   
        return args_handler
    
    def validate_run(self,info,log, run_code,out_stream, err_stream):
        """
        See super class.
        
        Return the unaltered run_code from the tool execution as exit_code.
        Unless an error note is found in the error stream. 
        """    
        if run_code != 0:            
            return(run_code,info)
            err_stream.seek(0)
#        if 'error' in err_stream.read():
#            log.error('found error note in err_stream')
#            return 1,info
        return 0,info
          
 
class IdXmlModifier(OpenMs):
    """
    Base class specifically for OpenMS tools that modify idXML files (e.g. for peptide-protein processing).
    """

    def __init__(self):
        """
        Constructor
        """
        super(IdXmlModifier,self).__init__()
        base = self.__class__.__name__
        self._result_file = '%s.idXML' % base # result produced by the application

    def prepare_run(self,info,log):
        """
        See interface.

        - Read the a specific template and replaces variables from the info object.
        - Tool is executed using the pattern: [PREFIX] -ini [TEMPLATE].
        - If there is a result file, it is added with a specific key to the info object.
        """
        wd = info[self.WORKDIR]
        log.debug('reset path of application files from current dir to work dir [%s]' % wd)
        self._template_file = os.path.join(wd,self._template_file)
        info['TEMPLATE'] = self._template_file
        self._result_file = os.path.join(wd,self._result_file)
        # have to temporarily set a key in info to store the original IDXML
        info['ORGIDXML'] = info['IDXML']
        info['IDXML'] = self._result_file
        log.debug('get template handler')
        th = self.get_template_handler()
        log.debug('modify template')
        mod_template,info = th.modify_template(info, log)
        # can delete temporary key as it is not longer needed
        del info['ORGIDXML']
        prefix,info = self.get_prefix(info,log)
        command = '%s -ini %s' % (prefix,self._template_file)
        return command,info

    def set_args(self,log,args_handler):
        """
        See interface
        """
        args_handler = super(IdXmlModifier, self).set_args(log,args_handler)
        args_handler.add_app_args(log, 'IDXML', 'The input idXML file ')
        return args_handler
    
class MzMlModifier(OpenMs):
    """
    Base class specifically for OpenMS tools that modify mzML files (e.g. for signal processing)
    """

    def __init__(self):
        """
        Constructor
        """
        super(MzMlModifier,self).__init__()
        base = self.__class__.__name__
        self._result_file = '%s.mzML' % base # result produced by the application

    def prepare_run(self,info,log):
        """
        See interface.

        - Read the a specific template and replaces variables from the info object.
        - Tool is executed using the pattern: [PREFIX] -ini [TEMPLATE].
        - If there is a result file, it is added with a specific key to the info object.
        """
        wd = info[self.WORKDIR]
        log.debug('reset path of application files from current dir to work dir [%s]' % wd)
        self._template_file = os.path.join(wd,self._template_file)
        info['TEMPLATE'] = self._template_file
        self._result_file = os.path.join(wd,self._result_file)
        # have to temporarily set a key in info to store the original IDXML
        info['ORGMZML'] = info['MZML']
        info['MZML'] = self._result_file
        log.debug('get template handler')
        th = self.get_template_handler()
        log.debug('modify template')
        mod_template,info = th.modify_template(info, log)
        # can delete temporary key as it is not longer needed
        del info['ORGMZML']
        prefix,info = self.get_prefix(info,log)
        command = '%s -ini %s' % (prefix,self._template_file)
        return command,info

    def set_args(self,log,args_handler):
        """
        See interface
        """
        args_handler = super(MzMlModifier, self).set_args(log,args_handler)
        args_handler.add_app_args(log, 'MZML', 'The input mzML file ')
        return args_handler    
