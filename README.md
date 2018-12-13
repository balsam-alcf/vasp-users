# VASP @ ALCF Theta 

**Author**: Ganesh Sivaraman (gsivaraman@anl.gov)

The [Vienna Ab initio Simulation Package [VASP], is a package for performing ab initio quantum mechanical calculations using either Vanderbilt pseudopotentials, or the projector augmented wave method, and a plane wave basis set.  We will cover some of the safe practices for using VASP on ALCF Theta HPC. 

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

# Launching VASP with Balsam workflow manager @ ALCF Theta 

