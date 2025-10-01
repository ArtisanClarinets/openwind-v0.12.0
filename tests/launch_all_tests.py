#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2019-2025, INRIA
#
# This file is part of Openwind.
#
# Openwind is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Openwind is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Openwind.  If not, see <https://www.gnu.org/licenses/>.
#
# For more informations about authors, see the CONTRIBUTORS file

import sys
import os
import subprocess
import time

pyfiles = [os.path.join(root, name)
           for root, dirs, files in os.walk(os.getcwd())
           for name in files
           if name.endswith(".py") and not name.startswith('TODO') and
           name not in ['launch_all_tests.py','update_howto.py',
                        'update_changelog.py']]


passed = list()
duration = list()

for pyfile in pyfiles:
    print('\n\n==============================\n' + pyfile
          + '\n==============================')
    t_start = time.time()
    passed.append(subprocess.call([sys.executable, pyfile]))
    duration.append(time.time() - t_start)

# %% Print

print('\n\n==============================\nGlobal Result'
      '\n==============================')
if any(passed):
    msg = ''
    for passed1, pyfile in zip(passed, pyfiles):
        if passed1:
            msg += 'The test "{}" failed! \n'.format(pyfile)
    raise ValueError(msg)
else:
    print('All tests passed!')

# %% Duration
t, title = (list(x) for x in zip(*sorted(zip(duration, pyfiles))))

for name, dt in zip(title, t):
    print(f"{dt:0.1f}: \t {name:s} ")
