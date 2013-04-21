#!/usr//bin/python

import sys
import re
import fileinput
import os
import shutil
import subprocess
import time
from datetime import datetime
import signal
import string
from threading import Timer

def build_under_bullseye(rundir, branch, covfile, full_path):
    os.environ['PATH'] = '/usr/bullseye/bin:/bin:/usr/local/bin:/usr/bin:/usr/kerberos/bin'
    #os.environ['COVFILE'] = os.path.join('/root', '.'.join([branch, 'cov']))
    os.environ['COVFILE'] = covfile
    print os.environ['COVFILE']
    os.chdir(rundir)
    if not os.path.exists(os.environ['SPLUNK_HOME']):
        os.mkdir(os.environ['SPLUNK_HOME'])
    subprocess.call(['/usr/bullseye/bin/cov01', '-1'])
    print os.environ
    time.sleep(60)
    subprocess.call(['./configure', '--disable-doxygen', 
                     '--without-unfinished-tests'], env=os.environ)
    if not os.path.exists(covfile):
        print 'covfile does not exist', covfile
        time.sleep(60)
    subprocess.call(['make', 'install'])
    if not os.path.exists(covfile):
        sys.exit('covfile does not exist')

    # Record time duration
    time1 = datetime.now()
    subprocess.call(['cmake/build_and_ctest.py', '-vO'])
    # Do some cleanup
    subprocess.call([os.path.join(os.environ['SPLUNK_HOME'], 'bin', 'splunk'), 'stop'])
    subprocess.call([os.path.join(os.environ['SPLUNK_HOME'], 'bin', 'splunk'), 'clean', 'all', '-f'])
    subprocess.call([os.path.join(os.environ['SPLUNK_HOME'], 'bin', 'splunk'), 'start'])
    time2 = datetime.now()
    delta = time2 - time1
    f = open(os.path.join(full_path, 'time_spent.log'), 'a')
    f.write("Ctest time spent (seconds):\n")
    f.write("%s" % str(delta.seconds))
    f.write("\n")
    f.close()
    
    subprocess.call(['/usr/bullseye/bin/cov01', '-0']) 

def checkout(build_dir_snippet, p4_dir='/home/eserv/perforce/splunk',
             depot='//qa-centos-amd64-05/splunk'):
    rundir = os.path.join(p4_dir, build_dir_snippet)
    sync_target = '/'.join([depot, build_dir_snippet, '...'])
    print sync_target
    if os.path.exists(rundir):
        shutil.rmtree(rundir)
    if not os.path.exists(p4_dir):
        os.mkdir(p4_dir)
    os.chdir(p4_dir)
    x = subprocess.call(['/usr/local/bin/p4', '-u', 'bamboo', '-P', 'symantec', 'sync', '-f',
                         sync_target])
    print 'checked out'
    print x

def kill_proc(proc, timeout):
    timeout["value"] = True
    py_version = sys.version_info[:2]
    print "timeout, kill process."
    if py_version > (2,5):
        proc.kill()
    else:
        os.kill(proc.pid, signal.SIGTERM)

def build_contrib(rundir):
    #os.chdir(os.path.join(rundir, 'contrib'))
    full_rundir = os.path.join(rundir, 'contrib')
    print 'SPLUNK_HOME: '
    print os.environ['SPLUNK_HOME']
    print os.path.isdir(os.environ['SPLUNK_HOME'])
    #x = subprocess.call(['./buildit.py'])
    buildit = os.path.join(full_rundir, 'buildit.py') 
    print buildit
    subprocess.call(['/usr/bullseye/bin/cov01', '-0'])
    p = subprocess.Popen(buildit, shell=True, cwd=full_rundir,
                         bufsize=1024, stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         close_fds=True)
    #while True:
    print p.stdout.read()
    x = p.wait()
    print 'built'
    print x
    return x

def kill_proc_and_release_port():
    # This is a utility function to kill process bound on port
    # 8000 and 8089
    cmd = '/usr/sbin/lsof -i TCP:%s'
    ports = ['8000', '8089']
    for eachPort in ports:
        proc = subprocess.Popen([cmd % eachPort], shell=True, bufsize=0, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        stdout, stderr = proc.communicate()
        if not stderr:
            if stdout:
                cmd_line = stdout.split('\n')
                if len(cmd_line) > 1:
                    second_line = cmd_line[1]
                    if second_line:
                        second_list = second_line.split()
                        if len(second_list) > 2:
                            pid = second_list[1]
                            if pid and isNumber(pid):
                                # Let us kill the process
                                print os.system('kill -9 ' + pid)

def isNumber(token):
    for char in token:
        if not char in string.digits: return False
    return True

def main(argv):
    os.environ['SPLUNK_HOME'] = '/home/eserv/splunk'
    os.environ['SPLUNK_DB'] = '/home/eserv/splunk/var/lib/splunk'
    os.environ['P4CLIENT'] = 'qa-centos-amd64-05'
    os.environ['PATH'] = os.environ['PATH'] + ':' + '/sbin'
    # To support multiple branch, default set to ace
    #branches_pool = {'bieber' : 'branches/bieber'}
    branches = {'current' : 'current'}
    #if len(argv) > 0:
    #    if argv[0][0:8] == "-branch=":
    #        if branches_pool.has_key(argv[0][8:]):
    #            branches = {argv[0][8:]: branches_pool[argv[0][8:]]}
    n = datetime.now()
    dirname = n.strftime('%Y-%m-%d-%H_%M')
    full_path = os.path.join('/home/eserv/bullseye_reports', dirname)
    if os.path.exists(full_path):
        shutil.rmtree(full_path)
    os.mkdir(full_path)
    for branch in branches:
        print branch
        branch_path = os.path.join(full_path, branch)
        os.mkdir(branch_path)
        dirname = branches[branch]
        covfile = '.'.join([branch, 'cov'])
        full_covfile = os.path.join('/home/eserv/bullseye_reports', covfile)
        if os.path.exists(full_covfile):
            os.remove(full_covfile)
        rundir = os.path.join('/home/eserv/perforce/splunk', dirname)
        print rundir

        # Kill hung process on port 8000 & 8089
        kill_proc_and_release_port()
        if os.path.exists(os.environ['SPLUNK_HOME']):
            shutil.rmtree(os.environ['SPLUNK_HOME'])
        os.mkdir(os.environ['SPLUNK_HOME'])
        checkout(dirname)
        x = build_contrib(rundir)
        if x:
            sys.exit('Could not build contrib')
        build_under_bullseye(rundir, branch, full_covfile, full_path)
        # After this, we need to archive Splunk build
        os.chdir('/home/eserv')
        proc = subprocess.Popen(['/bin/tar', 'czf', '/home/eserv/splunk_archive/splunk.tar.gz', 'splunk'], bufsize=0, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        stdout, stderr = proc.communicate()
        print "%s: %s" % ("full_path is", full_path)

if __name__ == '__main__':
    main(sys.argv[1:])
