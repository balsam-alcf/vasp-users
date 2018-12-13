# VASP @ ALCF Theta 

**Author**: Ganesh Sivaraman (gsivaraman@anl.gov)

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
[Balsam HPC workflow]: https://balsam.alcf.anl.gov/

# Launching VASP with Balsam workflow manager @ ALCF Theta 

In this section, We would see how to combined the knowledge gaining in launching single VASP jobs on Theta be used to running the same in ensemble mode using the [Balsam HPC workflow]. The reference dataset for this discussion can be found in The reference dataset for this discussion can be found in `vasp_balsam/h20/` and the balsam script in `vasp_balsam/vasp_to_balsamDB.py`. This script transfers individual VASP runs one by one in to a Balsam database. 

We will start with a brief discussion on the example python script. In this example, we will assume jobs belong three categories i.e. `'S', 'M', 'L'`. Each of them are classified based on different run times and resource requirement. For example the individual 'S'mall size jobs require just 10 minutes to converge ionic steps and runs on two nodes. There are 8 such jobs in our example. Similarly from a basic benchmark as shown in previous steps we can categorize jobs and create complex tree like run maps with in Balsam. Accordingly modify the follow lines in the script. 


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

```bash
module purge
module load balsam
module load cray-python/3.6.1.1
```

Once the modules are loaded, we will create a balsam database. 
```bash
balsam init testdb  ## Created a new Balsam DB with the name testdb.
source balsamactivate testdb 
```
In case DB was already created then only second line needs to be run (especially to log back in to Theta and check job status on an existing Balsam submission. Next we will check the status of the database  and then run the python script to load all of our Jobs in to the database. 

```bash
balsam ls --verbose         #--> Check status
python vasp_to_balsamDB.py  #---> YAY! Everything loaded to DB 
```

Finally we will submit the list stored in the database in to the Theta Cobalt job queue (i.e. similar to `qsub`). 

```bash
balsam submit-launch -t 60 -n 08  -q debug-cache-quad  --job-mode mpi -A PROJECTNAME #-->change  the value to -A parameter
```
The last run should produce an output  as shown below. 

```bash
Submit OK: Qlaunch {   'command': '/lus/theta-fs0/~/testdb/qsubmit/qlaunch1.sh',
    'from_balsam': True,
    'id': 1,
    'job_mode': 'mpi',
    'nodes': 8,
    'prescheduled_only': False,
    'project': 'datascience',
    'queue': 'debug-cache-quad',
    'scheduler_id': 296093,
    'state': 'submitted',
    'wall_minutes': 60,
    'wf_filter': ''}
```

**TIP4: Run `watch balsam ls --by-states` to see  a summary of the job submission*.* 

**TIP5: To check the convergence of VASP run `fgrep "Total CPU time used"   PATH/S/*/OUTCAR  | wc -l`. This should give you an idea of total number of folders that converged.** 

**Warning: Do not mix different versions of `Python`.**



