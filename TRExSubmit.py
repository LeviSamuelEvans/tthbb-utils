'''

    Python Script to run Condor batch jobs for different steps in TRExFitter 06.01.23 LE v1.0

    Need to optimise these features :
        1. The precedure for making the rror and output directories inside the script 
        2. The number fo submit files made through this, could potentially delete afterwards 
        3. Make it such that the script submit jobs in one large batch, instead of separately ( this will be a fair amount of work to do this )
        4. Send a notification to the user when the jobs ahve finished | or just send the error notification if jobs do not run for any reason 

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
            #submit_file.write("JOBDIR="+workDir+configName+"/"+region+"\n")
            #submit_file.write("mkdir -p $JOBDIR && cd $JOBDIR\n")
            submit_file.write("source /afs/cern.ch/user/l/leevans/TRExFitter/setup.sh\n")
            #submit_file.write("source /cvmfs/sft.cern.ch/lcg/releases/LCG_94/GSL/2.5/x86_64-slc6-gcc62-opt/GSL-env.sh")
            #submit_file.write("export LD_LIBRARY_PATH=/cvmfs/sft.cern.ch/lcg/releases/LCG_94/GSL/2.5/x86_64-slc6-gcc62-opt/lib:$LD_LIBRARY_PATH\n")
            submit_file.write(pathToExe+" "+actions+" "+config+"  \'"+opts+"\'\n")
            submit_file.write("echo $PWD \n")
            submit_file.write("ls -l \n")
            #submit_file.write("rm -rf $JOBDIR\n")
    
    '''

     Job Flavours can be the following :  

         espresso     = 20 minutes        
         microcentury = 1 hour           
         longlunch    = 2 hours          
         workday      = 8 hours          
         tomorrow     = 1 day            
         testmatch    = 3 days           
         nextweek     = 1 week           
     Alternatively you can set the job time in seconds using option :       
     +MaxRuntime = Number of seconds    -> set in the writehtcSubmit function instead of RunTime


    '''

    # Function to write 
    def writehtcSubmit(self, name, exe, logs, workdir, args = "NONE", RunTime = "21600", univ = "vanilla", cpus = "4", out="NONE", err="NONE"):
        '''
        File that writes a HTCondor submission script and returns it              
        '''
        workDir = workdir+"/submit_Feb23_Histograms/HTCondor/"
        self.mkdir(workDir)
        with open(workDir+name+".sub", "w") as submit_file:
            submit_file.write("executable = " + exe + "\n")
            if (args == "NONE"):
                submit_file.write("arguments = $(ClusterId)$(ProcId)\n")
            else:
                submit_file.write("arguments = " + args + "\n")
            if (out == "NONE"):
                submit_file.write("output = output_Feb23_HIstograms/"+name+"$(ClusterId)$(ProcId).out\n")
            else:
                submit_file.write("output = " + out + "\n")
            if (err == "NONE"):
                submit_file.write("error = error_Feb23_Histograms/"+name+"$(ClusterId)$(ProcId).err\n")
            else:
                submit_file.write("error = " + err + "\n")
            submit_file.write("log = " + logs + "\n")
            submit_file.write("requirements = (OpSysAndVer =?= \"CentOS7\" ) \n")
            submit_file.write("universe = " + univ + "\n")
            #submit_file.write("transfer_input_files = /usr/lib64/libgsl.so,/usr/lib64/libgsl.so.0,/usr/lib64/libgsl.so.0.16.0\n")
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
        configName = config.split('/')[-1].split('.')[0] # Assuming config file and fit have the same name, and fit name does not contain '.' characters.
        if region != '':
            submitName = configName+'_'+region
        else:
            submitName = configName
        logDir = workDir+'/logs/'+configName
        logFile = logDir+'/'+submitName+'.log'
        #args = actions+' '+config+' \''+opts+'\''

        pathToShScripts = workDir+"/submit_Feb23_Histograms/bashScripts/" # Path to executable for HTCondor
        pathToSubFile = workDir+"/submit_Feb23_Histograms/HTCondor/" # Path to HTCondor script
        
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

    
    #configsDir = '/eos/user/l/leevans/Fit_Studies_ttHbbLegacy/configs_STXS_sensitivity_1l/'
    #configsDir = '/eos/user/l/leevans/Fit_Studies_ttHbbLegacy/configs_TP_Jan23/'
    #configsDir  = '/eos/user/l/leevans/Fit_Studies_ttHbbLegacy/configs_PS_Channel_decorr_Jan23/'
    configsDir  =  '/eos/user/l/leevans/Fit_Studies_ttHbbLegacy/configs_TP_Feb23_newBaseline/'
    # You can add as many configs as you want, will run jobs for all of them. Make sure to put the output directory in the TRExFitter configs!
    listOfConfigs = [
        #configsDir + 'trial_config.yaml',
        #configsDir + 'config_2l_Baseline_Full_Jan23.yaml',
        #configsDir + 'config_2l_Compare_Baseline_Comb_ttgeq1b_scale_var_only_Jan23.yaml',
        #configsDir + 'config_2l_Full_Study_ttgeq1b_combined_sys_Jan23.yaml ',
        #configsDir + 'config_1l_Baseline_Full_Jan23.yaml',
        #configsDir + 'config_1l_STXS_26Bins_SR_Jan23.yaml',
        #configsDir + 'config_1l_STXS_30Bins_SR_Jan23.yaml',
        #configsDir + 'config_1l_STXS_38Bins_SR_Jan23.yaml',
        #configsDir + 'config_1l_STXS_42Bins_SR_Jan23.yaml',
        #configsDir + 'config_1l_Baseline_Full_Jan23.yaml',
        #configsDir + 'config_1l_Compare_Baseline_Comb_ttgeq1b_Jan23.yaml',
        #configsDir + 'config_1l_Compare_Baseline_Comb_ttgeq1b_scale_var_Jan23.yaml',
        #configsDir + 'config_CombinedFit_Baseline_Full_Jan23.yaml',
        #configsDir + 'config_CombinedFit_ttgeqb_all_Jan23.yaml',
        #configsDir + 'config_CombinedFit_ttgeqb_scale_Jan23.yaml',
        #configsDir  + 'config_CombinedFit_ttgeq1b_scale.yaml',
        #configsDir  + 'config_CombinedFit_ttgeq1b_All.yaml'
        #configsDir  + 'config_1l_PS_Channel_decorr_Jan23_ASIMOV.yaml',
        #configsDir  + 'config_1l_PS_Channel_decorr_Jan23_BONLY.yaml',
        #configsDir  + 'config_1l_PS_Channel_decorr_withCompCorr_Jan23_ASIMOV.yaml',
        #configsDir  + 'config_1l_PS_Channel_decorr_withCompCorr_Jan23_BONLY.yaml',
        #configsDir  + 'config_2l_PS_Channel_decorr_Jan23_ASIMOV.yaml',
        #configsDir  + 'config_2l_PS_Channel_decorr_Jan23_BONLY.yaml',
        #configsDir  + 'config_2l_PS_Channel_decorr_withCompCorr_Jan23_ASIMOV.yaml',
        #configsDir  + 'config_2l_PS_Channel_decorr_withCompCorr_Jan23_BONLY.yaml',
        #configsDir +  'config_Combined_PS_Channel_decorr_Jan23_ASIMOV.yaml',
        #configsDir +  'config_Combined_PS_Channel_decorr_Jan23_BONLY.yaml',
        #configsDir +  'config_Combined_PS_Channel_decorr_withCompCorr_Jan23_ASIMOV.yaml',
        #configsDir +  'config_Combined_PS_Channel_decorr_withCompCorr_Jan23_BONLY.yaml',
        #configsDir +  'config_1l_ttXS_decorr_region_Jan23_BONLY.yaml',
        #configsDir +  'config_2l_ttXS_decorr_region_Jan23_BONLY.yaml',
        #configsDir +  'config_combined_ttXS_decorr_region_Jan23_BONLY.yaml',
        #configsDir +  'config_1l_ttXS_decorr_SA_Jan23_BONLY.yaml',
        #configsDir +  'config_2l_ttXS_decorr_SA_Jan23_BONLY.yaml',
        #configsDir +  'config_1l_ttXS_decorr_sample_Jan23_BONLY.yaml',
        #configsDir +  'config_2l_ttXS_decorr_sample_Jan23_BONLY.yaml',
        #configsDir + 'config_1l_ttXS_NoHTReweight_Jan23_BONLY.yaml',
        #configsDir + 'config_2l_ttXS_NoHTReweight_Jan23_BONLY.yaml',
        configsDir  + 'config_1l_baseline_BONLY.yaml',
        configsDir  + 'config_2l_baseline_BONLY.yaml',

            ]
        

    #listOfConfigs = [
        #]

    # Path to compiled trex-fitter executable
    exePath = '/afs/cern.ch/user/l/leevans/TRExFitter/build/bin/trex-fitter'

    # working directory where output will be copied to
    workingDir = os.getcwd()
    
    # actions for TRExFitter
    #actions = 'i' # grouped systematics impact
    #actions = 'fp'# workspace and fit
    actions = 'n' # histogram-stage
    #actions = 'dp'
    #actions = 'f'
    #actions = 'dwfp'
    #actions = 'mwfp' # Combined-fit 
    # parallelise the jobs by submitting one job per region
    #runRegsSep = False
    runRegsSep = True 

    # Some extra options
    extraOpts = ()

    submitJobs = TRExSubmit(listOfConfigs, exePath, workingDir, actions, runRegsSep, extraOpts)

    submitJobs.runSubmit()
