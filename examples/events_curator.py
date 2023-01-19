"""
A script to generate neuroimaging event files from EPRIME text files.

Project: MAMABRAIN
Platform: Flywheel or standalone
Author: Amy Hegarty
Modified: 2023-01-18
"""


import pandas as pd
import os, sys
import numpy as np
import matplotlib.pyplot as plt
import argparse
from functools import partial
from pathlib import Path

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('main')

__version__ = "0.0.1"


def build_dataframe(dat):
    
    onsets = [i for i in dat.columns if ".OnsetTime" in i]
    log.info("Using OnsetTime for event onsets: \n%s", ", ".join(onsets))
    # OnsetTime: Time when E-Prime actually submitted the stimulus data for
    # presentation (e.g., proceeded to copy data to display memory or load
    # sound buffer)

    # get block
    blocks = dat["Running"]

    # stimulation type
    stimType = dat["StimType"]

    # Get block ID
    blockID = dat["ID"]

    # get ITI
    iti = dat["ITI"]

    # get fixation onset
    fixation_onset = [];
    fixcols = [i for i in onsets if "Fixation" in i] 
    for c in fixcols:
        if dat[c].dtype != np.number:
            vals=np.transpose(np.array(list(map(int,[sub.replace('.', '0') for sub in dat[c].values[:]]))))
        else:
            vals=dat[c]
        vals = vals[vals > 0]
        fixation_onset = np.concatenate((fixation_onset,vals))

    # get Response onset
    response_onset = [];
    respcols = [i for i in onsets if "Response" in i] 
    for c in respcols:
        if dat[c].dtype != np.number:
            vals = np.transpose(np.array(list(map(int, [sub.replace('.', '0') for sub in dat[c].values[:]]))))
        else:
            vals = dat[c]
        vals = vals[vals > 0]
        response_onset = np.concatenate((response_onset,vals))

    # get stimulus onset
    stimulus_onset = [];
    stimcols = [i for i in onsets if "Stimulus" in i] 
    for c in stimcols:
        if dat[c].dtype != np.number:
            vals = np.transpose(np.array(list(map(int, [sub.replace('.', '0') for sub in dat[c].values[:]]))))
        else:
            vals = dat[c]
        vals = vals[vals > 0]
        stimulus_onset = np.concatenate((stimulus_onset,vals))

    events = pd.DataFrame({"Blocks":blocks, "ID": blockID, "StimType": stimType, "Fixation.OnsetTime": fixation_onset,"Response.OnsetTime": response_onset,"Stimulus.OnsetTime": stimulus_onset})

    
    # Duration is the actual time between current action onset and next action onset (Event duration)
    durations = [i for i in dat.columns if ".Duration" in i]
    log.info("Using Duration for event durations: \n%s", ", ".join(durations))

    # get fixation onset
    fixation_duration = [];
    fixcols = [i for i in durations if "Fixation" in i] 
    for c in fixcols:
        if dat[c].dtype != np.number:
            vals = np.transpose(np.array(list(map(int, [sub.replace('.', '0') for sub in dat[c].values[:]]))))
        else:
            vals = dat[c]
        vals = vals[vals > 0]
        fixation_duration = np.concatenate((fixation_duration,vals))

    # get Response onset
    response_duration = [];
    respcols = [i for i in durations if "Response" in i] 
    for c in respcols:
        if dat[c].dtype != np.number:
            vals = np.transpose(np.array(list(map(int, [sub.replace('.', '0') for sub in dat[c].values[:]]))))
        else:
            vals = dat[c]
        vals = vals[vals > 0]
        response_duration = np.concatenate((response_duration,vals))

    # get stimulus onset
    stimulus_duration = [];
    stimcols = [i for i in durations if "Stimulus" in i] 
    for c in stimcols:
        if dat[c].dtype != np.number:
            vals = np.transpose(np.array(list(map(int, [sub.replace('.', '0') for sub in dat[c].values[:]]))))
        else:
            vals = dat[c]
        vals = vals[vals > 0]
        stimulus_duration = np.concatenate((stimulus_duration,vals))

    df = pd.DataFrame({"Fixation.Duration": fixation_duration, "Response.Duration": response_duration, "Stimulus.Duration": stimulus_duration, "WaitForScanner.OnsetTime": dat["WaitForScanner.OnsetTime"]})

    events = pd.concat([events,df], axis=1)
    
    return events



def build_block_events(df):
    # create event blocks

    groups = df['ID'].unique()

    onset = []; duration = [] ; name = []; offset = [];

    blocks = df["Blocks"].unique()

    # get the waiting for scanner time ( actual start of the data)
    time0 = df.iloc[0]["WaitForScanner.OnsetTime"]
    
    log.info("Creating event blocks...")
    log.info("Using %s", ", ".join(groups))
    log.info("Using timing offest set by WaitForScanner.OnsetTime: %s secs", str(time0/1000))

    for idx, x in enumerate(blocks):
        row1=df[df["Blocks"] == blocks[idx]].index[0]
        val1 = df.iloc[row1]["Stimulus.OnsetTime"]

        row2=df[df["Blocks"] == blocks[idx]].index[-1]
        val2 = df.iloc[row2]["Fixation.OnsetTime"] + df.iloc[row2]["Fixation.Duration"] - df.iloc[row1]["Stimulus.OnsetTime"]


        onset.append(val1-time0)
        duration.append(val2)
        offset.append(val1-time0+val2)
        name.append(df.iloc[row1]["ID"])

    outputs = pd.DataFrame({"onset": onset, "duration": duration, "trial_type": name})

    outputs["onset"] = outputs["onset"]/1000
    outputs["duration"] = outputs["duration"]/1000
    
    log.info("Complete")
    
    return outputs


def build_trial_events(df):
    # create stimulus related events

    groups = df['StimType'].unique()

    onset = []; duration = [] ; name = []; offset = [];

    # get the waiting for scanner time ( actual start of the data)
    time0 = df.iloc[0]["WaitForScanner.OnsetTime"]
    
    log.info("Creating stimulus based events...")
    log.info("Using %s", ", ".join(groups))
    log.info("Using timing offest set by WaitForScanner.OnsetTime: %s secs", str(time0/1000))

    for index, row in df.iterrows():
        val1 = row["Stimulus.OnsetTime"]
        val2 =  row["Response.OnsetTime"] + row["Response.Duration"] - row["Stimulus.OnsetTime"]

        onset.append(val1-time0)
        duration.append(val2)
        offset.append(val1-time0+val2)
        name.append(row["StimType"])

    outputs = pd.DataFrame({"onset": onset, "duration": duration, "trial_type": name})

    outputs["onset"] = outputs["onset"]/1000
    outputs["duration"] = outputs["duration"]/1000

    log.info("Complete")
    return outputs


def plot_blocks(outputs,ax):
   
    colors = plt.cm.Set1(np.linspace(0,1,len(outputs['trial_type'].unique())+1))

    for idg, g in enumerate(outputs['trial_type'].unique()):
        df = outputs[outputs['trial_type'] == g]
        df = df.reset_index(drop=True)

        for index, row in df.iterrows():
            if index == 0:
                ax.plot([row["onset"], row["onset"]+row["duration"]], [idg/5+1, idg/5+1], color=colors[idg], linewidth=2, label=g)
            else:
                ax.plot([row["onset"], row["onset"]+row["duration"]], [idg/5+1, idg/5+1], color=colors[idg], linewidth=2)


    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5));

    ax.set_yticks([]);
    ax.set_ylim((0, len(outputs['trial_type'].unique())+1));

    ax.set_title("Block Events");

    # Hide the right and top spines
    ax.spines[['right','top','bottom']].set_visible(False)

    
def plot_trials(outputs, ax):
    colors = plt.cm.Set1(np.linspace(0,1,len(outputs['trial_type'].unique())+1))

    for idg, g in enumerate(outputs['trial_type'].unique()):
        df = outputs[outputs['trial_type'] == g]
        df = df.reset_index(drop=True)

        for index, row in df.iterrows():
            if index == 0:
                ax.plot([row["onset"], row["onset"]], [idg-0.5, idg+0.5], color=colors[idg], linewidth=1, label=g)
            else:
                ax.plot([row["onset"], row["onset"]], [idg-0.5, idg+0.5], color=colors[idg], linewidth=1)


    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5));
    ax.set_yticks([]);
    ax.set_ylim((-0.5, len(outputs['trial_type'].unique())+0.5));

    ax.set_title("Trial by Trial Events");

    # Hide the right and top spines
    ax.spines[['right','top','bottom']].set_visible(False)

    

def main(file,outputpath):

    log.info('Deriving Events for file: %s', str(file))
    if not outputpath:
        outputpath = file.parents[0]

    #organize eprime file to needed columns only
    dat = pd.read_csv(file,delimiter='\t')
    events = build_dataframe(dat)
    
    # build and save block events file
    block_outputs = build_block_events(events)

    outname = os.path.join(outputpath,str(file.name).replace("_recording-eprime_stim.tsv","_block-events.tsv"))
    block_outputs.to_csv(outname,sep='\t',header=True, index=False)
    log.info("Outputs written: %s", outname)
    
    # build and save stimulus events file
    stim_outputs = build_trial_events(events)
    outname = os.path.join(outputpath,str(file.name).replace("_recording-eprime_stim.tsv","_events.tsv"))
    stim_outputs.to_csv(outname,sep='\t',header=True, index=False)
    log.info("Outputs written: %s", outname)

    # plot resulting events
    fig, ax = plt.subplots(nrows=2, ncols=1)
    fig.set_figwidth(10)
    fig.set_figheight(3)
    plt.subplots_adjust(left=0.05,
                    bottom=0.1,
                    right=0.9,
                    top=0.9,
                    wspace=0.4,
                    hspace=0.8)
    
    plot_blocks(block_outputs,ax[0])
    plot_trials(stim_outputs,ax[1])
    
    outname = os.path.join(outputpath,str(file.name).replace(".tsv",".png"))
    plt.savefig(outname)
    log.info("Events visualization written: %s", outname)
    
    

def parser(context):
    
    parser = argparse.ArgumentParser(
        description="Generates Event Onset and duration files for use in neuroimaging conputational modeling software (e.g. FEAT, CONN, AFNI). For use in MAMABRAIN study.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # parse inputs 

    def _path_exists(path, parser):
        """Ensure a given path exists."""
        if path is None or not Path(path).exists():
            raise parser.error(f"Path does not exist: <{path}>.")
        return Path(path).absolute()

    def _is_file(path, parser):
        """Ensure a given path exists and it is a file."""
        path = _path_exists(path, parser)
        if not path.is_file():
            raise parser.error(f"Path should point to a file (or symlink of file): <{path}>.")
        return path

    PathExists = partial(_path_exists, parser=parser)
    IsFile = partial(_is_file, parser=parser)

    ##########################
    #   Required Arguments   #
    ##########################
    parser.add_argument(
        "eprimefile",
        action="store",
        metavar="EPRIME.txt",
        type=PathExists,
        help="file path for eprime text file (tab delimited) used to generate events."
    )

    parser.add_argument(
        "--outputpath",
        action="store",
        metavar="PATH",
        type=PathExists,
        help="output path to store generated files (e.g. /flywheel/v0/outputs)"
    )

    args = parser.parse_args()

    # add all args to context
    args_dict = args.__dict__
    context.update(args_dict)
    


if __name__ == "__main__":

	
    # Welcome message
    welcome_str = '{} {}'.format('mambrain_events', __version__)
    welcome_decor = '=' * len(welcome_str)
    log.info('\n{}\n{}\n{}'.format(welcome_decor, welcome_str, welcome_decor))

    # run main
    pycontext = dict()
    parser(pycontext)

    main(pycontext["eprimefile"], pycontext["outputpath"])


# -----------------------------------------------------------------
# Flywheel Curator Functions. Do Not Change! 
#  (Consult INC team for instructions)
# -----------------------------------------------------------------
    
import os
import tempfile
import subprocess as sp
import backoff
import shutil
from flywheel.rest import ApiException
from flywheel_gear_toolkit.utils.curator import HierarchyCurator


def is_not_500_502_504(exc):
    if hasattr(exc, "status"):
        if exc.status in [504, 502, 500]:
            # 500: Internal Server Error
            # 502: Bad Gateway
            # 504: Gateway Timeout
            return False
    return True


@backoff.on_exception(
    backoff.expo, ApiException, max_time=60, giveup=is_not_500_502_504
)
# will retry for 60s, waiting an exponentially increasing delay between retries
# e.g. 1s, 2s, 4s, 8s, etc, giving up if exception is in 500, 502, 504.
def robust_upload(parent,filepath):
    if parent.get_file(os.path.basename(filepath)):
        log.info("file already exists %s \n Do Nothing.", os.path.basename(filepath))
        return
    parent.upload_file(filepath)
    log.info("uploaded file to %s", parent.label)


class Curator(HierarchyCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, extra_packages=["tqdm==4.59.0", "backoff==1.11.1"])
        # Curate depth first
        #   Important to curate depth first so that all files in curate_file
        #   Are guaranteed to be under the current self.sub_label
        self.config.depth_first = True
        self.data = {}

    def curate_subject(self, subject):
        self.data["sub_label"] = subject.label

    def curate_file(self, file_):
        if file_.type == "PsychoPy data":
            # Get parent of file
            parent_type = file_.parent_ref["type"]
            if parent_type != "acquisition":
                # Only curate acquisition files.
                return
            get_parent_fn = getattr(self.context.client, f"get_{parent_type}")
            parent = get_parent_fn(file_.parent_ref["id"])
            # Download EPRIME file, generate events files, and upload back to acquisition
            with tempfile.TemporaryDirectory() as temp:
                path = os.path.join(temp, file_.name)
                file_.download(path)

                # run main from above...                
                main(Path(path), Path(temp))
                
                # list of files to upload
                searchfiles = sp.Popen(
                    "cd " + temp + "; ls *.tsv ",
                    shell=True,
                    stdout=sp.PIPE,
                    stderr=sp.PIPE, universal_newlines=True
                )
                stdout, _ = searchfiles.communicate()

                filelist = stdout.strip("\n").split("\n")
                
                if file_.name in filelist: filelist.remove(file_.name)
                    
                log.info("Uploading files to aquisition %s: \n%s:",parent.label, "\n".join(filelist))
                
                for f in filelist:
                    robust_upload(parent, os.path.join(temp,f))

                # move output files to outputs folder
                searchfiles = sp.Popen(
                    "cd " + temp + "; ls * ",
                    shell=True,
                    stdout=sp.PIPE,
                    stderr=sp.PIPE, universal_newlines=True
                )
                stdout, _ = searchfiles.communicate()

                filelist = stdout.strip("\n").split("\n")
                
                if file_.name in filelist: filelist.remove(file_.name)

                for f in filelist:
                    shutil.move(os.path.join(temp,f), os.path.join('/flywheel/v0/output/',f))





