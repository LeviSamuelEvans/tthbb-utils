'''
   =================================================================================================
   === Python Script to run Condor batch jobs for different steps in TRExFitter 29.03.23 LE v1.0 ===
   =================================================================================================
    
    - v0.1 named TRExSubmit.py 06.01.23

    - v1.0 New features: 
        - Split by systematic as well as region | results in ~ 1000 batch jobs
        - Ignore commented out regions/systematics
        - Ignore if syst/reg name is enclosed by double quote
        - parse through syst names with ; separating them 

    Develop in this branch then merge in once ready.

    Need to optimise these features :
        1. The precedure for making the error and output directories inside the script ! Priority

'''


import sys, os

#from queue_management import count_queue_numbers, get_queue

class TRExSubmit :

    def __init__(self, listOfConfigs, pathToExe, workDir, actions, runRegsSep, runSystSep, extraOpts):
        self.listOfConfigs = listOfConfigs
        self.pathToExe     = pathToExe
        self.workDir       = workDir
        self.actions       = actions
        self.runRegsSep    = runRegsSep
        self.runSystSep    = runSystSep
        self.extraOpts     = extraOpts
    # Function to retrive regions defined in the yaml config file 

    def getRegionList(self, config):
        regList = []
        for line in open(config):
            lineStrip = line.split('%')[0].strip()
            if 'Region:' in lineStrip and 'FitRegion' not in lineStrip:
                reg = lineStrip.split(":")[1].strip()
                
                # Check if the region name is enclosed by double quotes
                if reg.startswith('"') and reg.endswith('"'):
                    reg = reg[1:-1]  # Remove the double quotes
                    
                regList.append(reg)
        return regList

    def getSystList(self, config):
        systList = []
        for line in open(config):
            lineStrip = line.split('%')[0].strip()
            if lineStrip.startswith('#'):
                continue
            if 'Systematic:' in lineStrip:
                syst_line = lineStrip.split(":")[1].strip()

                # Check if the systematic names are enclosed by double quotes
                if syst_line.startswith('"') and syst_line.endswith('"'):
                    syst_line = syst_line[1:-1]  # Remove the double quotes

                # Split the systematic names by semicolon and add them to the systList
                for syst in syst_line.split(';'):
                    print(syst)
                    systList.append(syst.strip())

        return systList


    
    # Function to facilitate the submission of jobs for each region
    def runSubmit(self):
        for config in self.listOfConfigs:
            if self.runRegsSep == True: # Parallelise the job submission by region.
                for reg in self.getRegionList(config):
                    if self.runSystSep == True:
                        for syst in self.getSystList(config):
                            self.jobSubmit(config, self.pathToExe, self.workDir, self.actions, region = reg, sample = syst, extraOpts = self.extraOpts)
                    else:
                        self.jobSubmit(config, self.pathToExe, self.workDir, self.actions, region = reg, extraOpts = self.extraOpts)
                        
            else:
                self.jobSubmit(config, self.pathToExe, self.workDir, self.actions, extraOpts = self.extraOpts)
    
    
    # Function to write the submission files to run in the Condor batch nodes 
    def writeSubmit(self, name, config, pathToExe, workDir, actions, region = '', sample = '', extraOpts = ()):
        configName = config.split('/')[-1].split('.')[0]
        if region != '':
            if sample != '':
                regOpt = ('Regions='+region+':Systematics='+sample+':SaveSuffix=_'+sample+'')
            else:
                regOpt = ('Regions='+region+'')
        else:
            regOpt = ''
        opts = ":".join((regOpt,)+extraOpts)
        
        with open(name, "w") as submit_file:
            submit_file.write("#!/bin/bash\n")
            submit_file.write("source /nfs/scratch4/levans/TRExFitter_v4.17/TRExFitter/setup.sh\n") # using version with ROOT 6.24/06 due to issues ( Report to Alex! )
            submit_file.write(pathToExe+" "+actions+" "+config+"  \'"+opts+"\'\n")
            submit_file.write("echo $PWD \n")
            submit_file.write("ls -l \n")
            #submit_file.write("rm -rf $JOBDIR\n")
    


    # Function to write 
    def writehtcSubmit(self, name, exe, logs, workdir, args = "NONE", RunTime = "14400", univ = "vanilla", cpus = "4", out="NONE", err="NONE"):
        '''
        File that writes a HTCondor submission script and returns it              
        '''
        workDir = workdir+"/submit_trial_samp_reg_split_histo/HTCondor/"
        self.mkdir(workDir)
        with open(workDir+name+".sub", "w") as submit_file:
            submit_file.write("executable = " + exe + "\n")
            if (args == "NONE"):
                submit_file.write("arguments = $(ClusterId)$(ProcId)\n")
            else:
                submit_file.write("arguments = " + args + "\n")
            if (out == "NONE"):
                submit_file.write("output = output_trial_samp_reg_split_histo/"+name+"$(ClusterId)$(ProcId).out\n") # rename output folder 
            else:
                submit_file.write("output = " + out + "\n")
            if (err == "NONE"):
                submit_file.write("error = error_trial_samp_reg_split_histo/"+name+"$(ClusterId)$(ProcId).err\n") # rename error folder 
            else:
                submit_file.write("error = " + err + "\n")
            submit_file.write("log = " + logs + "\n")
            submit_file.write("requirements = (OpSysAndVer =?= \"CentOS7\" ) \n")
            submit_file.write("universe = " + univ + "\n")
            submit_file.write("should_transfer_files = YES\n")
            submit_file.write("when_to_transfer_output = ON_EXIT\n")
            submit_file.write("+MaxRuntime = " + RunTime + "\n")
            submit_file.write("queue")

    def mkdir(self, directory):
        try:
            os.makedirs(directory)
        except:
            pass

    def jobSubmit(self, config, pathToExe, workDir, actions, region = '', sample = '', extraOpts = ()):
        configName = config.split('/')[-1].split('.')[0] 
        if region != '':
            if sample != '':
                submitName = configName+'_'+region+'_'+sample
            else:
                submitName = configName+'_'+region
        else:
            submitName = configName
        logDir = workDir+'/logs/'+configName
        logFile = logDir+'/'+submitName+'.log'
        #args = actions+' '+config+' \''+opts+'\''

        pathToShScripts = workDir+"/submit_trial_samp_reg_split_histo/bashScripts/" # Path to executable for HTCondor
        pathToSubFile = workDir+"/submit_trial_samp_reg_split_histo/HTCondor/" # Path to HTCondor script
        
        self.mkdir(pathToShScripts)

        self.writeSubmit(pathToShScripts+submitName+".sh", config, pathToExe, pathToShScripts, actions, region, sample, extraOpts = ())

        self.writehtcSubmit(submitName,
                pathToShScripts+submitName+".sh",
                logFile,
                workDir)

        condorSub = 'condor_submit '+pathToSubFile+submitName+".sub"

        self.mkdir(logDir)

        os.system(condorSub)


if __name__ == "__main__":

    
    #configsDir = '/eos/user/l/leevans/Fit_Studies_ttHbbLegacy/configs_STXS_sensitivity_1l/'
    #configsDir = '/eos/user/l/leevans/Fit_Studies_ttHbbLegacy/configs_TP_Jan23/'
    #configsDir  = '/eos/user/l/leevans/Fit_Studies_ttHbbLegacy/configs_PS_Channel_decorr_Jan23/'
    #configsDir  =  '/eos/user/l/leevans/Fit_Studies_ttHbbLegacy/configs_TP_Feb23_newBaseline/'
    #configsDir = '/nfs/scratch4/levans/legacy_fit_studies/Fit_Studies_Feb23/configs/'
    #configsDir = '/nfs/scratch4/levans/legacy_fit_studies/Fit_Studies_Mar23/configs_decorr_ttbar_supNP/'
    #configsDir = '/nfs/scratch4/levans/legacy_fit_studies/Fit_Studies_Mar23/configs_decorr_ttb_scale_var/'
    #configsDir = '/scratch4/levans/legacy_fit_studies/Fit_Studies_Apr23/configs/'
    configsDir = '/nfs/scratch4/levans/legacy_fit_studies/Fit_Studies_Apr23/configs_fakes/'
    # You can add as many configs as you want, will run jobs for all of them. Make sure to put the output directory in the TRExFitter configs!
    listOfConfigs = [
         configsDir + 'trial_sample_reg_split.yaml',
            ]


    # Path to compiled trex-fitter executable
    exePath = '/nfs/scratch4/levans/TRExFitter_v4.17/TRExFitter/build/bin/trex-fitter'

    # Working directory where output will be copied to
    
    workingDir = os.getcwd()
    
    #========================#
    # Actions for TRExFitter #
    #========================#
    
    #actions = 'i'    # grouped systematics impact
    #actions = 'fp'   # Individual fit and post-fit plots
    #actions = 'n'    # histogram-stage
    #actions = 'f'    # Individual fit 
    #actions = 'dwfp' # Pre-fit plots,workspace,fit and post-fit plots
    #actions = 'wfp'  # workspace,fit and post-fit plots
    #actions = 'mf'   # Combined-fit
    #actions = 'mfp'  # Combined-fit and post-fit plots
    #actions = 'mwfp' # Combined workspace,fit and post-fit plots
    #actions = 'r'    # Ranking 

    #============================#
    # Parallelise Job submission #
    #============================#

    #=== By Region ====

    #runRegsSep = False
    runRegsSep = True 

     #=== By Systematic ====

    #runSystSep = False
    runSystSep = True

    # Some extra options
    extraOpts = ()

    submitJobs = TRExSubmit(listOfConfigs, exePath, workingDir, actions, runRegsSep, runSystSep, extraOpts)

    submitJobs.runSubmit()
