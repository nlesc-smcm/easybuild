This repository contains EasyBuild scripts required to build Trilinos 12.14 with SuperLU_DIST support.
Job scripts are available for Peregrine and Cartesius.

Before you run the script, make sure you don't have your ((LD_)LIBRARY_)PATH set in your .bashrc, since this will make the compilation of the X11 module fail.

On Peregrine, an alternate installation path is required due to the inode limit on /home, and the huge amount of files that the compilation of Boost creates.
To make sure the modules are actually found after installation in this installation path, add the path to your module path:

```
module use /data/$USER/software/modules/all
```

or

```
export MODULEPATH=$MODULEPATH:/data/$USER/software/modules/all
```

After this you can load the Trilinos and CMake modules (and all of their dependencies) by using

```
module load Trilinos/12.14.1-intel-2019a-Python-3.7.2
module load CMake/3.13.3-GCCcore-8.2.0
```

You may also need to set the Intel MPI compilers as your default compilers

```
export CC=mpiicc
export CXX=mpiicpc
export FC=mpiifort
```