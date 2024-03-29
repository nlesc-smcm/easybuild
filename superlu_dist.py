##
# Copyright 2009-2018 Ghent University, University of Luxembourg
#
# This file is part of EasyBuild,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://www.vscentrum.be),
# Flemish Research Foundation (FWO) (http://www.fwo.be/en)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# https://github.com/easybuilders/easybuild
#
# EasyBuild is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation v2.
#
# EasyBuild is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EasyBuild.  If not, see <http://www.gnu.org/licenses/>.
##
"""
EasyBuild support for building and installing the SuperLU_DIST library, implemented as an easyblock

@author: Xavier Besseron (University of Luxembourg)
"""

import os
from distutils.version import LooseVersion

from easybuild.easyblocks.generic.cmakemake import CMakeMake
from easybuild.framework.easyconfig import CUSTOM
from easybuild.tools.build_log import EasyBuildError
from easybuild.tools.systemtools import get_shared_lib_ext
from easybuild.tools.modules import get_software_root, get_software_version, get_software_libdir


class EB_SuperLU_underscore_DIST(CMakeMake):
    """
    Support for building the SuperLU_DIST library
    """

    @staticmethod
    def extra_options():
        """
        Define custom easyconfig parameters for SuperLU_DIST.
        """
        extra_vars = {
            'build_shared_libs': [False, "Build shared library (instead of static library)", CUSTOM],
        }
        return CMakeMake.extra_options(extra_vars)

    def configure_step(self):
        """
        Set the CMake options for SuperLU_DIST
        """
        self.cfg['separate_build_dir'] = True

        if self.cfg['build_shared_libs']:
            self.cfg.update('configopts', '-DBUILD_SHARED_LIBS=ON')
            self.lib_ext = get_shared_lib_ext()

        else:
            self.cfg.update('configopts', '-DBUILD_SHARED_LIBS=OFF')
            self.lib_ext = 'a'

        # Add -fPIC flag if necessary
        pic_flag = ('OFF', 'ON')[self.toolchain.options['pic']]
        self.cfg.update('configopts', '-DCMAKE_POSITION_INDEPENDENT_CODE=%s' % pic_flag)

        # Make sure not to build the slow BLAS library included in the package
        self.cfg.update('configopts', '-DTPL_ENABLE_BLASLIB=OFF')

        # Set the BLAS library to use
        # For this, use the BLA_VENDOR option from the FindBLAS module of CMake
        # Check for all possible values at https://cmake.org/cmake/help/latest/module/FindBLAS.html
        toolchain_blas = self.toolchain.definition().get('BLAS', None)[0]
        if toolchain_blas == 'imkl':
            imkl_version = get_software_version('imkl')
            if LooseVersion(imkl_version) >= LooseVersion('10'):
                # 'Intel10_64lp' -> For Intel mkl v10 64 bit,lp thread model, lp64 model
                # It should work for Intel MKL 10 and above, as long as the library names stay the same
                # SuperLU_DIST requires thread, 'Intel10_64lp_seq' will not work!
                self.cfg.update('configopts', '-DBLA_VENDOR="Intel10_64lp"')

            else:
                # 'Intel' -> For older versions of mkl 32 and 64 bit
                self.cfg.update('configopts', '-DBLA_VENDOR="Intel"')

        elif toolchain_blas in ['ACML', 'ATLAS', 'FlexiBLAS']:
            self.cfg.update('configopts', '-DBLA_VENDOR="%s"' % toolchain_blas)

        elif toolchain_blas == 'OpenBLAS':
            # Unfortunately, OpenBLAS is not recognized by FindBLAS from CMake,
            # we have to specify the OpenBLAS library manually
            openblas_lib = os.path.join(get_software_root('OpenBLAS'), get_software_libdir('OpenBLAS'), "libopenblas.a")
            self.cfg.update('configopts', '-DBLAS_LIBRARIES="%s;-pthread"' % openblas_lib)

        elif toolchain_blas is None:
            # This toolchain has no BLAS library
            raise EasyBuildError("No BLAS library found in the toolchain")

        else:
            # This BLAS library is not supported yet
            raise EasyBuildError("BLAS library '%s' is not supported yet", toolchain_blas)

        super(EB_SuperLU_underscore_DIST, self).configure_step()

    def install_step(self):
        """
        Custom install procedure for SuperLU_DIST
        """
        super(EB_SuperLU_underscore_DIST, self).install_step()

        self.libbits = 'lib'
        if not os.path.exists(os.path.join(self.installdir, self.libbits)):
            self.libbits = 'lib64'

        if not os.path.exists(os.path.join(self.installdir, self.libbits)):
            raise EasyBuildError("No lib or lib64 subdirectory exist in %s", self.installdir)

        expected_libpath = os.path.join(self.installdir, self.libbits, "libsuperlu_dist.%s" % self.lib_ext)
        actual_libpath = os.path.join(self.installdir, self.libbits, "libsuperlu_dist_%s.%s" %
                                      (self.cfg['version'], self.lib_ext))

        if not os.path.exists(expected_libpath):
            try:
                os.symlink(actual_libpath, expected_libpath)
            except OSError as err:
                raise EasyBuildError("Failed to create symlink '%s' -> '%s: %s", expected_libpath, actual_libpath, err)

    def sanity_check_step(self):
        """
        Check for main library files for SuperLU_DIST
        """
        custom_paths = {
            'files': ["include/superlu_dist_config.h", os.path.join(self.libbits, "libsuperlu_dist.%s" % self.lib_ext)],
            'dirs': [],
        }
        super(EB_SuperLU_underscore_DIST, self).sanity_check_step(custom_paths=custom_paths)
