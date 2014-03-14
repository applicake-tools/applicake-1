"""
Created on 13 May 2013

@author: lorenz
"""

import os
import subprocess
import shutil
import getpass

from applicake.framework.keys import Keys
from applicake.framework.templatehandler import BasicTemplateHandler
from applicake.applications.proteomics.openbis.dropbox import Copy2Dropbox
from applicake.framework.informationhandler import IniInformationHandler
from applicake.utils.dictutils import DictUtils


class Copy2IdentDropbox(Copy2Dropbox):
    def main(self, info, log):
        """
        See super class.
        """
        #TODO: simplify "wholeinfo" apps
        #re-read INPUT to get access to whole info, needs set_args(INPUT). add runnerargs to set_args if modified by runner
        ini = IniInformationHandler().get_info(log, info)
        info = DictUtils.merge(log, info, ini)

        info['WORKFLOW'] = self._extendWorkflowID(info['WORKFLOW'])
        info['DROPBOXSTAGE'] = self._make_stagebox(log, info)

        keys = ['PEPXMLS', 'PEPCSV']
        self._keys_to_dropbox(log, info, keys, info['DROPBOXSTAGE'])

        #protxml special naming
        filename = os.path.basename(info['DROPBOXSTAGE']) + '.prot.xml'
        filepath = os.path.join(info['DROPBOXSTAGE'], filename)
        shutil.copy(info['PROTXML'], filepath)

        #search.properties requires some specific fields
        info['PEPTIDEFDR'] = info['PEPTIDEFDR']
        info['DBASENAME'] = os.path.splitext(os.path.split(info['DBASE'])[1])[0]
        info['PARENT-DATA-SET-CODES'] = info[Keys.DATASET_CODE]

        # set values to NONE if they were e.g. "" before
        check_keys = ['STATIC_MODS', 'VARIABLE_MODS']
        for key in check_keys:
            if not info.has_key(key) or info[key] == "":
                info[key] = 'NONE'
        info['experiment-code'] = self._get_experiment_code(info)

        sinfo = info.copy()
        sinfo[Keys.OUTPUT] = os.path.join(info['DROPBOXSTAGE'], 'search.properties')
        IniInformationHandler().write_info(sinfo, log)

        info['EXPERIMENT_CODE'] = info['experiment-code']
        info['ENGINES_VERSIONS'] = ''
        if 'RUNTANDEM' in info and info['RUNTANDEM'] == 'True':
            info['ENGINES_VERSIONS'] += subprocess.check_output("tandem a | grep TANDEM",
                                                                shell=True)

        if 'RUNOMSSA' in info and info['RUNOMSSA'] == 'True':
            info['ENGINES_VERSIONS'] += subprocess.check_output("omssacl -version", shell=True).replace(
                "2.1.8", "2.1.9")

        if 'RUNMYRIMATCH' in info and info['RUNMYRIMATCH'] == 'True':
            info['ENGINES_VERSIONS'] += subprocess.check_output("myrimatch 2>&1 | grep MyriMatch",
                                                                shell=True)

        if 'RUNCOMET' in info and info['RUNCOMET'] == 'True':
            info['ENGINES_VERSIONS'] += subprocess.check_output("comet 2>&1 | grep version", shell=True)

        info['TPPVERSION'] = subprocess.check_output("InteractParser 2>&1 | grep TPP", shell=True).split("(")[1]
        info['USERNAME'] = getpass.getuser()

        info[Keys.TEMPLATE] = os.path.join(info['DROPBOXSTAGE'], 'mailtext.txt')
        _, info = MailTemplate().modify_template(info, log)

        info['DROPBOXSTAGE'] = self._move_stage_to_dropbox(info['DROPBOXSTAGE'], info['DROPBOX'], keepCopy=True)

        return 0, info


class MailTemplate(BasicTemplateHandler):
    def read_template(self, info, log):
        if not 'RUNTANDEM' in info:
            log.info("No key RUNTANDEM found, skipping mail creation")
            return

        template = """Dear $USERNAME

Your TPP search workflow finished sucessfully!

"""

        if info['RUNPETUNIA'] == 'none':
            template += """RUNPETUNIA was none. If you want to visualize the results, run the tpp2viewer2.py script on tpp2:
[user@imsb-ra-tpp2~] # cd ~/html/petunia; tpp2viewer2.py $EXPERIMENT_CODE

Then use these links:
https://imsb-ra-tpp2.ethz.ch/browse/$USERNAME/html/petunia/tpp2viewer_$EXPERIMENT_CODE.pep.shtml
https://imsb-ra-tpp2.ethz.ch/browse/$USERNAME/html/petunia/tpp2viewer_$EXPERIMENT_CODE.prot.shtml

"""
        else:
            template += """To visualize the results use:
https://imsb-ra-tpp2.ethz.ch/browse/$USERNAME/html/petunia/tpp2viewer_$EXPERIMENT_CODE.pep.shtml
https://imsb-ra-tpp2.ethz.ch/browse/$USERNAME/html/petunia/tpp2viewer_$EXPERIMENT_CODE.prot.shtml

In case the links do not work run the tpp2viewer2.py script on tpp2:
[user@imsb-ra-tpp2~] # cd ~/html/petunia; tpp2viewer2.py $EXPERIMENT_CODE

"""

        template += """To cite this workflow use:
The spectra were searched using the search engines
${ENGINES_VERSIONS}against the $DBASE database using $ENZYME digestion and allowing $MISSEDCLEAVAGE missed cleavages.
Included were '$STATIC_MODS' as static and '$VARIABLE_MODS' as variable modifications. The mass tolerances were set to $PRECMASSERR $PRECMASSUNIT for precursor-ions and $FRAGMASSERR $FRAGMASSUNIT for fragment-ions.
The identified peptides were processed and analyzed through the Trans-Proteomic Pipeline ($TPPVERSION) using PeptideProphet, iProphet and ProteinProphet scoring. Peptide identifications were reported at FDR of $PEPTIDEFDR.
    
Yours sincerely,
The iPortal team
    
Please note that this message along with your results are stored in openbis:
https://ra-openbis.ethz.ch/openbis/#action=BROWSE&entity=EXPERIMENT&project=/$SPACE/$PROJECT"""

        return template, info


