from __future__ import with_statement
from fabric.api import *
from fabric.contrib.console import confirm

import os
import shutil
import datetime

tar_file = 'pygpw.tar'
bz2_file = tar_file+'.bz2'
tar_infiles = ['pygpw.py', 'pygpw_tris.py', 'LICENSE.TXT']
sec_divider = '-'*50
cleanable_files = ['*.pyc', '*.pyo', '*.cpickle']

def _sprn(s):
    """print a section/title with emphasis"""
    print '\n%s\n%s\n%s' % (sec_divider, s.upper(), sec_divider)

    
def _delete_silently(filename):
    """try best to delete a file, but dont break control flow"""
    if os.path.exists(filename):
        try:
            os.remove(filename)
        except:
            print "there was an error deleting", filename, ", ignoring..."
            pass
    else:
        print 'file was not found, skipping...'
        
def maketar():
    _sprn('tar-ing')
    _delete_silently(tar_file)
    local('tar cvf %s %s' % (tar_file, ' '.join(tar_infiles)), capture=False)
    print '%s bytes'% os.stat(tar_file).st_size
    _sprn('bzipping')
    _delete_silently(bz2_file)
    local('bzip2 -9 %s' % tar_file, capture=False)
    print '%s bytes' % os.stat(bz2_file).st_size


def clean():
    _sprn('cleaning')
    del_cmd = 'rm -rvf'
    if os.name == 'nt':
        del_cmd = 'del /F /S'
    local('%s %s' % (del_cmd, ' '.join(cleanable_files)), capture=False)
