import argparse
import os
from balsam.core.models import BalsamJob, ApplicationDefinition
from django.core.exceptions import ObjectDoesNotExist

EXE_PATH = '/soft/applications/vasp/vasp6-dev/bin/vasp_std'
APPNAME = 'vasp' # Any alias you want
INPUTNAME = 'INCAR' # Create a job for each folder that holds this filename
NNODES = 4 # Number of nodes to run on
RPN = 32 # Number of MPI ranks per node
TPR = 2 # Number of OpenMP threads per MPI rank

def new_job(name, workdir, workflow_tag):
    '''Create a new BalsamJob object *without* saving it to DB'''
    return BalsamJob(
        name=name,
        user_workdir=workdir, # the job will run inside this directory
        workflow = workflow_tag,
        application = APPNAME,
        num_nodes=NNODES,
        ranks_per_node=RPN,
        threads_per_rank=TPR,
        cpu_affinity='depth',
    )

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--top-dir',
        help="This folder and its subfolders will be searched for input files, and a new job \
        will be created for each one", required=True
    )
    parser.add_argument('--wf-tag',
        help='A unique tag to categorize this batch \
        of jobs (for instance, "prod-batch_32")', required=True
    )
    return parser.parse_args()

def bootstrap_app():
    '''Ensure App is already in the DB'''
    try:
        app = ApplicationDefinition.objects.get(name=APPNAME)
        assert os.path.isfile(app.executable)
    except ObjectDoesNotExist:
        assert os.path.isfile(EXE_PATH)
        app = ApplicationDefinition(
            name=APPNAME,
            executable=EXE_PATH
        )
        app.save()

def main():
    args = get_args()
    wf_tag = args.wf_tag
    top_dir = os.path.abspath(os.path.expanduser(args.top_dir))
    assert os.path.isdir(top_dir)
    bootstrap_app()

    # Get a list of all user_workdirs *already* registered in the DB
    # This way, we will never double-create a BalsamJob for the same directory
    existing_job_paths = list(BalsamJob.objects.values_list('user_workdir', flat=True))

    # Recursively walk through all subdirectories of top_dir
    # Create a job for each subdirectory that holds a file matching INPUTNAME
    for (dirpath, dirnames, filenames) in os.walk(top_dir):
        if INPUTNAME in filenames:
            workdir = os.path.abspath(os.path.join(top_dir, dirpath))
            if workdir in existing_job_paths: continue # already exists; skip it
            job = new_job(
                name=os.path.basename(dirpath),
                workdir=workdir, 
                workflow_tag=wf_tag
            )
            job.save()
            print('new job', job.cute_id, 'will run in:', workdir)

if __name__ == "__main__": main()
