#!/bin/bash

/home/eserv/bullseye_coverage_scripts/add_clustering/run_bullseye_stage1.py $1
export COVFILE=/home/eserv/bullseye_reports/current.cov
source /home/eserv/splunk/bin/setSplunkEnv
cd /home/eserv/perforce/splunk/current/new_test
source /home/eserv/perforce/splunk/current/new_test/setTestEnv
cp /home/eserv/bullseye_coverage_scripts/add_clustering/conftest.py /home/eserv/perforce/splunk/current/new_test/tests/clustering/search
cp /home/eserv/bullseye_coverage_scripts/add_clustering/__init__.py /home/eserv/perforce/splunk/current/new_test/tests/clustering/search
patch /home/eserv/perforce/splunk/current/new_test/tests/clustering/search/test_batch_mode.py /home/eserv/bullseye_coverage_scripts/add_clustering/patch.diff
/home/eserv/bullseye_coverage_scripts/add_clustering/run_bullseye_stage2.py $1
# After run Bullseye, copy over the coverage files to esnas
# and them clean the /usr/local/bullseye_reports directory
#cp -r --remove-destination /home/eserv/bullseye_reports/* /mnt/bullseye_report_new

#rm -rf /home/eserv/bullseye_reports/*
# We also want to clean up SPLUNK_HOME, and source
#rm -rf /home/eserv/splunk/current/*
#rm -rf /home/eserv/perforce/splunk/*
#source /home/eserv/.bash_profile
