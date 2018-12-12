# VASP @ ALCF Theta 

**Author**: Ganesh Sivaraman (gsivaraman@anl.gov)

The [Vienna Ab initio Simulation Package [VASP][1], is a package for performing ab initio quantum mechanical calculations using either Vanderbilt pseudopotentials, or the projector augmented wave method, and a plane wave basis set.  We will cover some of the safe practices for using VASP on ALCF Theta HPC. 

The reference dataset for this discussion can be found in `~/VASP_BALSAM/vasp_benchmarks/h20/`. There are two fundamental levels of parameters that one must be aware of while running the VASP. The first level refers to the parameters that are embedded in the VASP INCAR file. 

```bash
NPAR = 8  #--> i.e.  \sqrt{\#ofcore}
NCORE = 8 #--> Optional parameter 
```

The second level refers to the parameters that regulate the aprun parameters. The following two parameters are safe recommendation to be kept in the  `submit-theta.sh` script. For our benchmark dataset the following parameter was found to be optimal. 

```bash
export n_mpi_ranks_per_node=16
export n_openmp_threads_per_rank=4
```

Always set `NPAR = 8`  in the `INCAR` file. Optional parameter is `NCORE = 8`. `NCORE` is automatically overridden if `(n_openmp_threads_per_rank or OMP_NUM_THREADS) > 1`. The analysis of the benchmark can be seen below.

![Bar plot of the total  run times](~/VASP_BALSAM/vasp_benchmarks/analysis/benchmark.png)

16 MPI-ranks per core and  4 OpenMP thread/rank seems to be the best set of parameters for this benchmark.

For  VASP tutorials the users are referred to their manual pages[3].  The detailed overview of the best practices of using VASP on Intel KNL is provided by [NERSC][4].  Our benchmarks are based on a number of best practices recommended by the aforementioned slides.



## References
[1]: https://en.wikipedia.org/wiki/Vienna_Ab_initio_Simulation_Package
[2]: https://cms.mpi.univie.ac.at/wiki/index.php/NPAR
[3]: http://cms.mpi.univie.ac.at/wiki/index.php/The_VASP_Manual
[4]: https://www.nersc.gov/assets/Uploads/Using-VASP-at-NERSC-20180629.pdf

# Launching VASP with Balsam workflow manager @ ALCF Theta 

