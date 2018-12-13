import balsam.launcher.dag as dag
from balsam.core.models import BalsamJob, ApplicationDefinition
import os
import glob
import sys
import subprocess


EXE_VASP = '/soft/applications/vasp/vasp6-dev/bin/vasp_std'
INPUTS_PATH = '/PATH/vasp_balsam/h20' # Change path to whatever!
sizes = 'S M L'.split()

TIME_MAP = {
            'S' : 10,
            'M' : 20,
            'L' : 40
           }
NNODES_MAP = {
            'S' : 2,
            'M' : 4,
            'L' : 8
           }

RPN = 32
TPR = 2

def create_app():
    '''define the VASP app'''
    app = ApplicationDefinition()
    app.name = 'vasp-scf'
    app.description = 'Run vasp 6.x'
    app.executable = EXE_VASP
    app.save()


def create_job_nocommit(name, size):
    '''Create a "job" row in the table without saving it (for faster bulk_insert)'''
    dirpath = os.path.join(INPUTS_PATH, size, name)


    job = dag.add_job(save=False, 
                      workflow=size,
                      name=name,
                      description=f'system name = {name} ',
                      user_workdir=dirpath,
                      wall_time_minutes=TIME_MAP[size],
                      num_nodes=NNODES_MAP[size],
                      ranks_per_node=RPN,
		      threads_per_rank = TPR,
                      threads_per_core = 1,	
                      cpu_affinity='depth',
                      application='vasp-scf',
                      auto_timeout_retry = True,
                      post_timeout_handler = False,
                      post_error_handler = False,
                     )
    return job


def main(dry_run=False):
    has_vasp = ApplicationDefinition.objects.filter(name='vasp-scf').exists()
    if not has_vasp: create_app()

    existing_jobnames = BalsamJob.objects.all().values_list('name', flat=True)

    for size in sizes:
        if size in os.listdir(INPUTS_PATH):
            dirpath = os.path.join(INPUTS_PATH, size)
            names = [j for j in glob.glob(dirpath + '/*') 
                if os.path.isdir(j) and os.path.exists(j+'/INCAR')]
            names = [os.path.basename(j) for j in names]

            new_jobs = [create_job_nocommit(name, size)
                    for name in names
                    if name not in existing_jobnames
                   ]
            print(f"Found {len(new_jobs)} jobs for size {size}")
            if not dry_run:
            	BalsamJob.objects.bulk_create(new_jobs)
            	print("Added to DB.")

if __name__ == "__main__":
    dry_run = any('dry' in arg for arg in sys.argv)
    main(dry_run)

