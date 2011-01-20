#!/usr/bin/env python
'''
Created on Jan 19, 2011

@author: quandtan
'''
import os,sys,shutil
from applicake.app import SequenceTemplateApplication

class Interact(SequenceTemplateApplication):
    
    def _get_command(self,prefix,input_filename):
        config = self._iniFile.read_ini()
        pepxml_filename = config['PEPXML']        
        db_filename = config['DBASE']
        self._result_filename  = os.path.join(self._wd, self.name  + '.pepxml')
        self._iniFile.add_to_ini({'INTERACT':self._result_filename})
        self.log.debug("add key 'INTERACT' with value [%s] to ini" % self._result_filename)

        # prefix is for this class a [] instead of a string
        prefixes = prefix
        self.log.debug('prefixes [%s]' %prefixes)
        if len(prefixes) != 3:
            self.log.fatal('number of prefixes is not correct [%s]' % len(prefixes))
            sys.exit(1)        
        params = open(input_filename,'r').readlines()
        self.log.debug('splitted params [%s]' %params)
        cmd = None
        if not len(prefixes)==len(params):
            self.log.fatal('number of prefixes [%s] does not match number of params [%s]' % (len(prefixes),len(params)))
            sys.exit(1)
        else:
            cmds = []
            # InteractParser <outfile> <file1.pep.xml> <file2.pep.xml>... <options>
            cmds.append('%s %s %s %s' % (prefixes[0],self._result_filename,pepxml_filename,params[0]))
            #RefreshParser <xmlfile> <database> (<min ntt>) (DEGEN) (PROT_MW) (PREV_AA_LEN=<length(default=1)>) (NEXT_AA_LEN=<length(default=1)>) (RESTORE_NONEXISTENT_IF_PREFIX=str)
            cmds.append('%s %s %s %s' % (prefixes[1],self._result_filename,db_filename,params[1]))
            #PeptideProphetParser output.pep.xml DECOY=DECOY_ MINPROB=0 NONPARAM
            cmds.append('%s %s %s' % (prefixes[2],self._result_filename,params[2]))            
        
        return ';'.join(cmds)
    
    def _validate_run(self,run_code):                
        exit_code = super(Interact, self)._validate_run(run_code)
        if 0 != exit_code:
            return exit_code

        return 0       

if "__main__" == __name__:
    # init the application object (__init__)
    a = Interact(use_filesystem=True,name=None)
    # call the application object as method (__call__)
    exit_code = a(sys.argv)
    #copy the log file to the working dir
    for filename in [a._log_filename,a._stderr_filename,a._stdout_filename]:
        shutil.move(filename, os.path.join(a._wd,filename))
    print(exit_code)
    sys.exit(exit_code)    
        