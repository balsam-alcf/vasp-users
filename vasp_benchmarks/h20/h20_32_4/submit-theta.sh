#!/bin/bash
#COBALT -t 00:60:00
#COBALT -n 2
#COBALT --attrs mcdram=cache:numa=quad
#COBALT -A datascience
#COBALT --queue debug-cache-quad
echo "Starting Cobalt job script"
export n_nodes=$COBALT_JOBSIZE
export n_mpi_ranks_per_node=32
export n_mpi_ranks=$(($n_nodes * $n_mpi_ranks_per_node))
export n_openmp_threads_per_rank=4
export n_hyperthreads_per_core=2
export n_hyperthreads_skipped_between_ranks=4
export bin=/soft/applications/vasp/vasp6-dev/bin/vasp_std

# Script example derived from here:
# https://www.alcf.anl.gov/user-guides/running-jobs-xc40
echo $bin
aprun -n $n_mpi_ranks -N $n_mpi_ranks_per_node \
  --env OMP_NUM_THREADS=$n_openmp_threads_per_rank -cc depth \
  -d $n_hyperthreads_skipped_between_ranks \
  -j $n_hyperthreads_per_core \
  $bin

