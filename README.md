# VASP @ ALCF Theta 

**Authors**: Ganesh Sivaraman (gsivaraman@anl.gov), Misha Salim (msalim@anl.gov)

The Vienna Ab initio Simulation Package [VASP], is a package for performing ab initio quantum mechanical calculations using either Vanderbilt pseudopotentials, or the projector augmented wave method, and a plane wave basis set.  We will cover some of the safe practices for using VASP on ALCF Theta HPC. 

The reference dataset for this discussion can be found in `vasp_benchmarks/h20/`. There are two fundamental levels of parameters that one must be aware of while running the VASP. The first level refers to the parameters that are embedded with in the VASP `INCAR` file. 

```bash
NPAR = 8  #--> i.e.  \sqrt{\#ofcore}
NCORE = 8 #--> Optional parameter 
```

The second level refers to the parameters that regulate the aprun parameters. The following two parameters are safe recommendation to be kept in the  `submit-theta.sh` script. For our benchmark dataset the following parameter was found to be optimal. 

```bash
export n_mpi_ranks_per_node=32
export n_openmp_threads_per_rank=2
```

**TIP1: [Always set] `NPAR = 8`  in the `INCAR` file.**

**TIP2: The best set of parameters  that came out of this benchmark are `32` MPI-ranks per core and  `2` OpenMP thread/rank as shown below.**

**TIP3: To restart a VASP run please use the [ISTART parameter] in INCAR file. A detailed discussion of the same is available in the online manual.**

**Warning : The `64` MPI-ranks per core and  `1` OpenMP thread/rank are not recommended as per  VASP manual and our benchmarks exited with out success.**

![Bar plot of the total  run times](vasp_benchmarks/analysis/benchmark.png)

Optional parameter is `NCORE = 8`  . `NCORE` is automatically overridden if `(n_openmp_threads_per_rank or OMP_NUM_THREADS) > 1`. 
For  VASP tutorials the users are referred to the online [manual pages].  The detailed overview of the best practices of using VASP on Intel KNL is provided by [NERSC].  Our benchmarks are based on a number of best practices recommended by the aforementioned slides.


[VASP]: https://en.wikipedia.org/wiki/Vienna_Ab_initio_Simulation_Package
[Always set]: https://cms.mpi.univie.ac.at/wiki/index.php/NPAR
[manual pages]: http://cms.mpi.univie.ac.at/wiki/index.php/The_VASP_Manual
[NERSC]: https://www.nersc.gov/assets/Uploads/Using-VASP-at-NERSC-20180629.pdf
[ISTART parameter]: http://cms.mpi.univie.ac.at/wiki/index.php/ISTART
[Balsam]: https://balsam.alcf.anl.gov/

# Launching VASP with Balsam Workflow Manager @ ALCF Theta 

## Getting started with Balsam on Theta
In this section, we use the [Balsam] tool to manage running a large ensemble of
VASP jobs on Theta over time.  The reference dataset for this discussion
can be found in `vasp_balsam/h20/`. We are assuming that a large directory of calculation
inputs already exists here, and we want to run VASP once in each subfolder that contains an
*INCAR* file.  

This straightforward to do with Balsam and consists of the following steps:

1. Initialize a new Balsam database for your project 
2. Define each calculation as a **BalsamJob** object in the database. 
3. Submit Balsam **Launcher** jobs to actually run the calculations! 

Letting Balsam run things for you provides several benefits:

- You no longer need to think about writing shell scripts for each job: Balsam handles
the `qsub` and `aprun` commands for you.
- Balsam automatically tracks the state of each calculation: you get useful logs from
failed runs, automatic-retry of timed-out runs, and so on
- The Django/SQL backend of Balsam makes it easy to query your workflow  status from Python
and make modifications
- When you feel comfortable, it's easy to add post-processing logic to automate handling errors or
parse calculation output and put it somewhere else
- The Balsam DB contains a Postgres JSONB datastore that lets you associate arbitrary data with each job,
using the familiar Python dictionary data structure.  Subsequent queries are efficient and simple like:
`BalsamJob.objects.filter(data__scf_energy__lte=-1000.0)`. 
- Execution metadata is automatically recorded for you and Balsam makes it easy
  to visualize detailed project statistics like job throughput and compute node
  utilization over time. This granularity of information for ensemble jobs is otherwise
  very hard to obtain.

Let's get started by loading the necessary Balsam modules on Theta.

```bash
module purge
module load balsam
module load cray-python/3.6.1.1
```

Once the modules are loaded, we can create a new Balsam database for our
project: 

```bash
balsam init /projects/myProject/testdb  ## Create a new Balsam DB
source balsamactivate testdb
```

**Note:** This database can live anywhere on the Theta filesystem. Preferably,
it should be created in the /projects/ subfolder that belongs to your ALCF
project. This file system is better suited for production, and group
permissions can be easily set here for collaboration with other users. Once a
database is created, it will persist on disk and hold the entire state and
history of your workflow, so that you can easily track a large campaign of jobs
over the course of many weeks and Cobalt job submissions.

**Note:** To connect to an existing database in future sessions, do not reinitialize it, but
simply activate the server with the second `source balsamactivate` command.


## Adding VASP calculations to Balsam: simple case
While it is possible to add jobs to Balsam with the `balsam job` command, this
is cumbersome for a large number of calculations.  Let's automate the process
with a Python script.  We start with the simplest example in
`vasp_balsam/vasp-insert.py`.  Each calculation is assumed to take the same
`aprun` parameters and differ only in the working directory. These parameters
are defined as module-level constants in the script as follows:

```python
EXE_PATH = '/soft/applications/vasp/vasp6-dev/bin/vasp_std'
APPNAME = 'vasp' # Any alias you want
INPUTNAME = 'INCAR' # Create a job for each folder that holds this filename
NNODES = 4 # Number of nodes to run on
RPN = 32 # Number of MPI ranks per node
TPR = 2 # Number of OpenMP threads per MPI rank

```

The goal is to create one BalsamJob for each subdirectory containing a filename
matching `INPUTNAME`. In our example, the script will visit each subfolder of some
top-level directory and create a job for each subfolder if it contains a `"INCAR"` 
file. The script checks for already-registered jobs to avoid duplicating a job for
the same folder.

We can invoke this script by providing two arguments the top-level folder to search with 
The script is invoked by providing two arguments: 

- `--top-dir` gives the top-level directory which is scanned recursively and
  searched for subdirectories containing `INCAR` files.
- `--wf-tag` should be a unique tag categorizing this batch of jobs to run. It
  is for organizational purposes and facilitates future database queries, so
  name it however you see fit.

Let's try running the script in the current directory:

```bash
python vasp-insert.py --top-dir=. --wf-tag=test  # All subfolders of cwd loaded to DB 
balsam ls # list all the jobs that were added to the DB
balsam ls --help # show many flexible options for listing jobs
```

Once some jobs are in the database, we simply need to fire off a `balsam
launcher` job to actually run them! Skip ahead to the section **Launching and 
Monitoring Jobs** if you are ready to try this out.

## Tuning number of nodes according to calculation subdirectory
In this example, we will assume jobs belong three categories i.e. `'S', 'M',
'L'`. Each of them are classified based on different run times and resource
requirement. For example the individual 'S'mall size jobs require just 10
minutes to converge ionic steps and runs on two nodes. There are 8 such jobs in
our example. Similarly from a basic benchmark as shown in previous steps we can
categorize jobs and create complex tree like run maps with in Balsam.
The script in `vasp_balsam/vasp_to_balsamDB.py` provides this flexibility. 

**Note:** The runtimes are only estimates provided for Balsam scheduling, which
is not used in this tutorial. The actual values have no bearing on how long
your jobs will actually run for (i.e. you can severely over or under-estimate the runtime).  


```python
INPUTS_PATH = '/PATH/vasp_balsam/h20' # Change path to whatever!
sizes = 'S M L'.split()  # e.g. INPUTS_PATH + '/S' should be in path!

```

In our example we have only considered 'S'. So make sure there is an 'S' folders corresponding to the  classification 'S' placed inside the  `INPUTS_PATH`. All of the runs  folders for 'S' are placed there. The runs times and nodes are controlled by the follow parameters.

```python
TIME_MAP = {
            'S' : 10, #--> Run time for single job in minutes
            'M' : 20,
            'L' : 40
           }
NNODES_MAP = {
            'S' : 2, #--> Nodes requested for a single job
            'M' : 4,
            'L' : 8
           }

RPN = 32 #--> MPI ranks  from our plot
TPR = 2  #--> Threads from our plot
```

Now let us look at some Balsam specific parameters. 

```python
auto_timeout_retry = True, #-->If 'True', retry job in case of aprun time outs
post_timeout_handler = False,
post_error_handler = False, #-->If 'True' add user defined function to handle error!
```
Now that we have went through explaining the script, let us look at how to run the script and query the status. Load the necessary modules and make sure all of the above changes are added to the python script. 


In case DB was already created then only second line needs to be run (especially to log back in to Theta and check job status on an existing Balsam submission. Next we will check the status of the database  and then run the python script to load all of our Jobs in to the database. 

```bash
balsam ls --verbose         #--> Check status
python vasp_to_balsamDB.py  #---> YAY! Everything loaded to DB 
```

## Launching and monitoring jobs

Finally we will submit the list stored in the database in to the Theta Cobalt job queue (i.e. similar to `qsub`). 

```bash
balsam submit-launch -t 60 -n 08  -q debug-cache-quad  --job-mode mpi -A PROJECTNAME #-->change  the value to -A parameter
```

The last run should produce an output as shown below. 

```bash
Submit OK: Qlaunch {   'command': '/lus/theta-fs0/~/testdb/qsubmit/qlaunch1.sh',
    'from_balsam': True,
    'id': 1,
    'job_mode': 'mpi',
    'nodes': 8,
    'prescheduled_only': False,
    'project': 'PROJECTNAME',
    'queue': 'debug-cache-quad',
    'scheduler_id': 296093,
    'state': 'submitted',
    'wall_minutes': 60,
    'wf_filter': ''}
```

The `command` shows a path to a script named
`qlaunchX.sh` which is the *actual* shell script that was submitted to Cobalt by Balsam on your behalf.
You can modify the template of this script (e.g. to define global environment variables or load
modules necessary for the workflow) located in `~/.balsam/job-templates`.

**TIP4: Run `watch balsam ls --by-states` to see  a summary of the job submission and count how many jobs are finished/running/failed.** 

**TIP5: For quick debugging, `balsam ls --state FAILED --history` will show the tail of stdout/stderr from each failed job.** 

**TIP6: To reset FAILED jobs for running again, you may want to use the Python API as shown below.**

```python
from balsam.launcher.dag import BalsamJob
failed = BalsamJob.objects.filter(state=FAILED)
failed = failed.filter(name__icontains='sim3', workflow='test') # optional; additional filters
BalsamJob.batch_update_state(failed, 'RESTART_READY')

```

**TIP7: To confirm the convergence of VASP run `fgrep "Total CPU time used"   PATH/S/*/OUTCAR  | wc -l`. This should give you an idea of total number of folders that converged. This should agree with the JOB_FINISHED count from balsam ls --by-states command** 

**Warning: POTCAR cannot be provided due to licensing issues. Copy your own!`.**

**Warning: Do not mix different versions of `Python`.**



