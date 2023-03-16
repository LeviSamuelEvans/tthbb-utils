'''

    Python Script to run Condor batch jobs for different steps in TRExFitter 06.01.23 LE v0.1

    Need to optimise these features :
        1. The precedure for making the error and output directories inside the script | implement same structure as log file creation
        2. The number fo submit files made
        3. Make it such that the script submit jobs in one large batch, instead of separately
        4. Send a notification to the user when the jobs ahve finished 

'''


import sys, os

#from queue_management import count_queue_numbers, get_queue

class TRExSubmit :

    def __init__(self, listOfConfigs, pathToExe, workDir, actions, runRegsSep, extraOpts):
        self.listOfConfigs = listOfConfigs
        self.pathToExe     = pathToExe
        self.workDir       = workDir
        self.actions       = actions
        self.runRegsSep    = runRegsSep
        self.extraOpts     = extraOpts
    # Function to retrive regions defined in the yaml config file 
    def getRegionList(self, config):
        regList = []
        for line in open(config):
            lineStrip = line.split('%')[0].strip()
            if 'Region:' in lineStrip and 'FitRegion' not in lineStrip:
                reg = lineStrip.split(":")[1].strip()
                regList.append(reg)
        return regList
        print (reglist)
    
    # Function to facilitate the submission of jobs for each region
    def runSubmit(self):
        for config in self.listOfConfigs:
            if self.runRegsSep == True: # Parallelise the job submission by region.
                for reg in self.getRegionList(config):
                    self.jobSubmit(config, self.pathToExe, self.workDir, self.actions, region = reg, extraOpts = self.extraOpts)
            else:
                self.jobSubmit(config, self.pathToExe, self.workDir, self.actions, extraOpts = self.extraOpts)
    
    # Function to write the submission files to run in the Condor batch nodes 
    def writeSubmit(self, name, config, pathToExe, workDir, actions, region = '', extraOpts = ()):
        configName = config.split('/')[-1].split('.')[0]
        regOpt = ('Regions='+region+'' if region != '' else '')
        opts = ":".join((regOpt,)+extraOpts)
        
        with open(name, "w") as submit_file:
            submit_file.write("#!/bin/bash\n")
            submit_file.write("source /nfs/scratch4/levans/TRExFitter_v4.17/TRExFitter/setup.sh\n") 
            submit_file.write(pathToExe+" "+actions+" "+config+"  \'"+opts+"\'\n")
            submit_file.write("echo $PWD \n")
            submit_file.write("ls -l \n")


    # Function to write 
    def writehtcSubmit(self, name, exe, logs, workdir, args = "NONE", RunTime = "6300", univ = "vanilla", cpus = "4", out="NONE", err="NONE"):
        '''
        File that writes a HTCondor submission script and returns it              
        '''
        workDir = workdir+"submit_decorr_ttb_scar_var_study/HTCondor/"
        self.mkdir(workDir)
        with open(workDir+name+".sub", "w") as submit_file:
            submit_file.write("executable = " + exe + "\n")
            if (args == "NONE"):
                submit_file.write("arguments = $(ClusterId)$(ProcId)\n")
            else:
                submit_file.write("arguments = " + args + "\n")
            if (out == "NONE"):
                submit_file.write("output = output_decor_ttb_scale/"+name+"$(ClusterId)$(ProcId).out\n")
            else:
                submit_file.write("output = " + out + "\n")
            if (err == "NONE"):
                submit_file.write("error = error_decor_ttb_scale/"+name+"$(ClusterId)$(ProcId).err\n")
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
    def jobSubmit(self, config, pathToExe, workDir, actions, region = '', extraOpts = ()):
        configName = config.split('/')[-1].split('.')[0] 
        if region != '':
            submitName = configName+'_'+region
        else:
            submitName = configName
        logDir = workDir+'/logs/'+configName
        logFile = logDir+'/'+submitName+'.log'
        #args = actions+' '+config+' \''+opts+'\''

        pathToShScripts = workDir+"submit_decorr_ttb_scar_var_study/bashScripts/" # Path to executable for HTCondor
        pathToSubFile = workDir+"submit_decorr_ttb_scar_var_study/HTCondor/" # Path to HTCondor script
        
        self.mkdir(pathToShScripts)

        self.writeSubmit(pathToShScripts+submitName+".sh", config, pathToExe, pathToShScripts, actions, region, extraOpts = ())

        self.writehtcSubmit(submitName,
                  pathToShScripts+submitName+".sh",
                  logFile,
                  workDir)

        condorSub = 'condor_submit '+pathToSubFile+submitName+".sub"
        print(pathToSubFile)
        print(submitName)


        self.mkdir(logDir)

        
        os.system(condorSub)

if __name__ == "__main__":

    
    configsDir = '/nfs/scratch4/levans/legacy_fit_studies/Fit_Studies_Mar23/configs_decorr_ttb_scale_var/'
    # You can add as many configs as you want, will run jobs for all of them. Make sure to put the output directory in the TRExFitter configs!
    listOfConfigs = [
        configsDir + 'trial_config.yaml',
            ]

    # Path to compiled trex-fitter executable
    exePath = '/nfs/scratch4/levans/TRExFitter_v4.17/TRExFitter/build/bin/trex-fitter'

    # working directory where output will be copied to
    workingDir = os.getcwd()
    
    ##########################
    # Actions for TRExFitter #
    ##########################
    
    #actions = 'i' # grouped systematics impact
    #actions = 'fp'# workspace and fit
    #actions = 'n' # histogram-stage
    #actions = 'f'
    #actions = 'dwfp'
    #actions = 'wfp'
    #actions = 'mf'
    #actions = 'mfp' # Combined-fit 
    #actions = 'mwfp'


    ## Parallelise the jobs by submitting one job per region ##

    runRegsSep = False
    #runRegsSep = True 

    # Some extra options
    extraOpts = ()

    submitJobs = TRExSubmit(listOfConfigs, exePath, workingDir, actions, runRegsSep, extraOpts)

    submitJobs.runSubmit()
