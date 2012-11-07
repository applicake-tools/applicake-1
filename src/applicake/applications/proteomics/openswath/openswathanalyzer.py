'''
Created on Jul 11, 2012

@author: quandtan
'''

import os
from applicake.framework.interfaces import IWrapper
from applicake.framework.templatehandler import BasicTemplateHandler
from applicake.utils.fileutils import FileUtils
from applicake.utils.xmlutils import XmlValidator

class OpenSwathAnalyzer(IWrapper):
    '''
    Wrapper for the MRMAnalyzer in OpenSWATH.
    '''

    _template_file = ''
    _result_file = ''
    _default_prefix = 'OpenSwathAnalyzer'


    def __init__(self):
        """
        Constructor
        """
        base = self.__class__.__name__
        self._template_file = '%s_template.ini' % base # application specific config file
        self._result_file = '%s.featureXML' % base # result produced by the application

    def get_prefix(self,info,log):
        if not info.has_key(self.PREFIX):
            info[self.PREFIX] = self._default_prefix
            log.debug('set [%s] to [%s] because it was not set before.' % (self.PREFIX,info[self.PREFIX]))
        return info[self.PREFIX],info

    def get_template_handler(self):
        """
        See interface
        """
        #return BasicTemplateHandler()
        return MRMAnalyzerTemplate()

    def prepare_run(self,info,log):
        """
        See interface.

        - Define path to result file (depending on work directory)
    - If a template is used, the template is read variables from the info object are used to set concretes.
        - If there is a result file, it is added with a specific key to the info object.
        """
        key = 'FEATUREXML' #self._file_type.upper()
        wd = info[self.WORKDIR]
        log.debug('reset path of application files from current dir to work dir [%s]' % wd)
        self._result_file = os.path.join(wd,self._result_file)
        info[key] = self._result_file
        self._template_file = os.path.join(wd,self._template_file)
        info['TEMPLATE'] = self._template_file
        log.debug('get template handler')
        th = self.get_template_handler()
        log.debug('modify template')
        mod_template,info = th.modify_template(info, log)
        prefix,info = self.get_prefix(info,log)
        command = '%s -in %s -tr %s -min_upper_edge_dist %s -threads %s -rt_norm %s -swath_files %s -ini %s -out %s' % (prefix,
                                                                                              info['CHROM_MZML'],
                                                                                              info['TRAML'],
                                                                                              info['MIN_UPPER_EDGE_DIST'],
                                                                                              info['THREADS'],
                                                                                              info['TRAFOXML'],
                                                                                              info['MZML'],
                                                                                              info[self.TEMPLATE],
                                                                                              self._result_file)
        return command,info

    def set_args(self,log,args_handler):
        """
        See super class.
        """      
        args_handler.add_app_args(log, self.WORKDIR, 'Directory to store files')
        args_handler.add_app_args(log, self.PREFIX, 'Path to the executable')
        args_handler.add_app_args(log, self.COPY_TO_WD, 'List of files to store in the work directory') 
        args_handler.add_app_args(log, self.TEMPLATE, 'Path to the template file')
        args_handler.add_app_args(log, 'THREADS', 'Number of threads used in the process.') 
        args_handler.add_app_args(log, 'CHROM_MZML', 'Path to the chrom.mzML files.')
        args_handler.add_app_args(log, 'TRAFOXML', 'Path to the .trafoXML files.')        
        args_handler.add_app_args(log, 'MZML', 'Path to the gzipped mzML files.')  
        args_handler.add_app_args(log, 'TRAML', 'Path to the TraML file.')      
        args_handler.add_app_args(log, 'MIN_UPPER_EDGE_DIST','')    
        return args_handler

    def validate_run(self,info,log, run_code,out_stream, err_stream):
        """
        See super class.
        """
        if 0 != run_code:
            return run_code,info
    #out_stream.seek(0)
    #err_stream.seek(0)
        if not FileUtils.is_valid_file(log, self._result_file):
            log.critical('[%s] is not valid' %self._result_file)
            return 1,info
        if not XmlValidator.is_wellformed(self._result_file):
            log.critical('[%s] is not well formed.' % self._result_file)
            return 1,info    
        return 0,info


class MRMAnalyzerTemplate(BasicTemplateHandler):
    """
    Template handler for MRMAnalyzer.
    """
    def read_template(self, info, log):
        """
        See super class.
        """
		
        template = """<?xml version="1.0" encoding="ISO-8859-1"?>
<PARAMETERS version="1.3" xsi:noNamespaceSchemaLocation="http://open-ms.sourceforge.net/schemas/Param_1_3.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <NODE name="OpenSwathAnalyzer" description="Picks peaks and finds features in an SRM experiment.">
    <ITEM name="version" value="1.10.0" type="string" description="Version of the tool that generated this parameters file." tags="advanced" />
    <NODE name="1" description="Instance &apos;1&apos; section for &apos;OpenSwathAnalyzer&apos;">
      <ITEM name="in" value="" type="string" description="input file containing the chromatograms." tags="input file,required" restrictions="*.mzML" />
      <ITEM name="tr" value="" type="string" description="transition file" tags="input file,required" restrictions="*.TraML" />
      <ITEM name="rt_norm" value="" type="string" description="RT normalization file (how to map the RTs of this run to the ones stored in the library)" tags="input file" restrictions="*.trafoXML" />
      <ITEM name="out" value="" type="string" description="output file" tags="output file,required" restrictions="*.featureXML" />
      <ITEM name="no-strict" value="false" type="string" description="run in non-strict mode and allow some chromatograms to not be mapped." restrictions="true,false" />
      <ITEMLIST name="swath_files" type="string" description="Swath files that were used to extract the transitions. If present, SWATH specific scoring will be applied." tags="input file" restrictions="*.mzML">
      </ITEMLIST>
      <ITEM name="min_upper_edge_dist" value="$MIN_UPPER_EDGE_DIST" type="float" description="Minimal distance to the edge to still consider a precursor, in Thomson (only in SWATH)" />
      <ITEM name="log" value="" type="string" description="Name of log file (created only when specified)" tags="advanced" />
      <ITEM name="debug" value="0" type="int" description="Sets the debug level" tags="advanced" />
      <ITEM name="threads" value="$THREADS" type="int" description="Sets the number of threads allowed to be used by the TOPP tool" />
      <ITEM name="no_progress" value="false" type="string" description="Disables progress logging to command line" tags="advanced" restrictions="true,false" />
      <ITEM name="test" value="false" type="string" description="Enables the test mode (needed for internal use only)" tags="advanced" restrictions="true,false" />
      <NODE name="model" description="Options to control the modeling of retention time transformations from data">
        <ITEM name="type" value="linear" type="string" description="Type of model" tags="advanced" restrictions="linear,b_spline,interpolated" />
        <ITEM name="symmetric_regression" value="false" type="string" description="Only for &apos;linear&apos; model: Perform linear regression on &apos;y - x&apos; vs. &apos;y + x&apos;, instead of on &apos;y&apos; vs. &apos;x&apos;." tags="advanced" restrictions="true,false" />
        <ITEM name="num_breakpoints" value="5" type="int" description="Only for &apos;b_spline&apos; model: Number of breakpoints of the cubic spline in the smoothing step. The breakpoints are spaced uniformly on the retention time interval. More breakpoints mean less smoothing. Reduce this number if the transformation has an unexpected shape." tags="advanced" restrictions="2:" />
        <ITEM name="interpolation_type" value="cspline" type="string" description="Only for &apos;interpolated&apos; model: Type of interpolation to apply." tags="advanced" />
      </NODE>
      <NODE name="algorithm" description="Algorithm parameters section">
        <ITEM name="stop_report_after_feature" value="-1" type="int" description="Stop reporting after feature (ordered by quality; -1 means do not stop)." />
        <ITEM name="rt_extraction_window" value="300" type="float" description="Only extract RT around this value (-1 means extract over the whole range, a value of 500 means to extract around +/- 500 s of the expected elution). For this to work, the TraML input file needs to contain normalized RT values." />
        <ITEM name="rt_normalization_factor" value="100" type="float" description="The normalized RT is expected to be between 0 and 1. If your normalized RT has a different range, pass this here (e.g. it goes from 0 to 100, set this value to 100)" />
        <ITEM name="quantification_cutoff" value="0" type="float" description="Cutoff below which peaks should not be used for quantification any more" tags="advanced" restrictions="0:" />
        <ITEM name="write_convex_hull" value="false" type="string" description="Whether to write out all points of all features into the featureXML" tags="advanced" restrictions="true,false" />
        <ITEM name="add_up_spectra" value="1" type="int" description="Add up spectra around the peak apex (needs to be a non-even integer)" tags="advanced" restrictions="1:" />
        <ITEM name="spacing_for_spectra_resampling" value="0.005" type="float" description="If spectra are to be added, use this spacing to add them up" tags="advanced" restrictions="0:" />
        <NODE name="TransitionGroupPicker" description="">
          <ITEM name="sgolay_frame_length" value="15" type="int" description="The number of subsequent data points used for smoothing.#br#This number has to be uneven. If it is not, 1 will be added." />
          <ITEM name="sgolay_polynomial_order" value="3" type="int" description="Order or the polynomial that is fitted." />
          <ITEM name="gauss_width" value="50" type="float" description="Gaussian width in seconds, estimated peak size." />
          <ITEM name="use_gauss" value="true" type="string" description="Use gauss for smoothing (other option is sgolay)" />
          <ITEM name="peak_width" value="40" type="float" description="Estimated peak width in seconds." restrictions="0:" />
          <ITEM name="signal_to_noise" value="1" type="float" description="Signal to noise." restrictions="0:" />
          <ITEM name="sn_win_len" value="1000" type="float" description="Signal to noise window length." />
          <ITEM name="sn_bin_count" value="30" type="int" description="Signal to noise bin count." />
          <ITEM name="stop_after_feature" value="-1" type="int" description="Stop finding after feature (ordered by intensity; -1 means do not stop)." />
          <ITEM name="stop_after_intensity_ratio" value="0.0001" type="float" description="Stop after reaching intensity ratio" />
          <ITEM name="stop_report_after_feature" value="-1" type="int" description="Stop reporting after feature (ordered by quality; 1 means do not stop)." />
          <ITEM name="background_subtraction" value="none" type="string" description="Try to apply a background subtraction to the peak (experimental). The background is estimated at the peak boundaries, either the smoothed or the raw chromatogram data can be used for that." restrictions="none,smoothed,original" />
        </NODE>
        <NODE name="DIAScoring" description="">
          <ITEM name="dia_extraction_window" value="0.05" type="float" description="DIA extraction window in Th." restrictions="0:" />
          <ITEM name="dia_centroided" value="false" type="string" description="Use centroded DIA data." restrictions="true,false" />
          <ITEM name="dia_byseries_intensity_min" value="300" type="float" description="DIA b/y series minimum intensity to consider." restrictions="0:" />
          <ITEM name="dia_byseries_ppm_diff" value="10" type="float" description="DIA b/y series minimal difference in ppm to consider." restrictions="0:" />
          <ITEM name="dia_nr_isotopes" value="4" type="int" description="DIA nr of isotopes to consider." restrictions="0:" />
          <ITEM name="dia_nr_charges" value="4" type="int" description="DIA nr of charges to consider." restrictions="0:" />
        </NODE>
        <NODE name="EMGScoring" description="">
          <ITEM name="interpolation_step" value="0.2" type="float" description="Sampling rate for the interpolation of the model function." tags="advanced" />
          <ITEM name="tolerance_stdev_bounding_box" value="3" type="float" description="Bounding box has range [minimim of data, maximum of data] enlarged by tolerance_stdev_bounding_box times the standard deviation of the data." tags="advanced" />
          <ITEM name="max_iteration" value="500" type="int" description="Maximum number of iterations using by Levenberg-Marquardt algorithm." tags="advanced" />
          <ITEM name="deltaAbsError" value="0.0001" type="float" description="Absolute error used by the Levenberg-Marquardt algorithm." tags="advanced" />
          <ITEM name="deltaRelError" value="0.0001" type="float" description="Relative error used by the Levenberg-Marquardt algorithm." tags="advanced" />
          <NODE name="statistics" description="">
            <ITEM name="mean" value="1" type="float" description="Centroid position of the model." tags="advanced" />
            <ITEM name="variance" value="1" type="float" description="Variance of the model." tags="advanced" />
          </NODE>
        </NODE>
        <NODE name="Scores" description="">
          <ITEM name="use_shape_score" value="true" type="string" description="Use the shape score" tags="advanced" restrictions="true,false" />
          <ITEM name="use_coelution_score" value="true" type="string" description="Use the coelution score" tags="advanced" restrictions="true,false" />
          <ITEM name="use_rt_score" value="true" type="string" description="Use the retention time score" tags="advanced" restrictions="true,false" />
          <ITEM name="use_library_score" value="true" type="string" description="Use the library score" tags="advanced" restrictions="true,false" />
          <ITEM name="use_elution_model_score" value="true" type="string" description="Use the elution model (EMG) score" tags="advanced" restrictions="true,false" />
          <ITEM name="use_intensity_score" value="true" type="string" description="Use the intensity score" tags="advanced" restrictions="true,false" />
          <ITEM name="use_nr_peaks_score" value="true" type="string" description="Use the number of peaks score" tags="advanced" restrictions="true,false" />
          <ITEM name="use_total_xic_score" value="true" type="string" description="Use the total XIC score" tags="advanced" restrictions="true,false" />
          <ITEM name="use_sn_score" value="true" type="string" description="Use the SN (signal to noise) score" tags="advanced" restrictions="true,false" />
        </NODE>
      </NODE>
    </NODE>
  </NODE>
</PARAMETERS>
"""
        log.debug('read template from [%s]' % self.__class__.__name__)
        return template,info
