#! /usr/bin/env python

from   distutils.core import setup
import py2exe, matplotlib, sys

path = sys.path[0]

sys.path.append(path + r'/input_windows')
sys.path.append(path + r'/database')
sys.path.append(path + r'/solvers')
sys.path.append(path + r'/postprocess')

files = matplotlib.get_py2exe_datafiles()
files.append(('', ['capsimicon.ico']))
#files.append(('batch_files', ['batch_files/one_layer_example.txt']))
#files.append(('batch_files', ['batch_files/multiple_run_example.txt']))
#files.append(('batch_files', ['batch_files/two_layer.txt']))


setup(
    data_files = files,
    options    = {'py2exe':
                  {'packages':     ['matplotlib', 'pytz'],
                   'excludes':     ['_gtkagg', '_tkagg'],
                   'dll_excludes': ['MSVCP90.dll', 'libgdk-win32-2.0-0.dll',
                                    'libgobject-2.0-0.dll', 
                                    'libgdk_pixbuf-2.0-0.dll',
                                    'tcl84.dll', 'tk84.dll']
                   }
                  },
    windows    = [{
            'script': 'capsim.py',
            'icon_resources': [(0, 'capsimicon.ico')]
            }
                  ],
    )
