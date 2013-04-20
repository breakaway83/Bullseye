#!/bin/bash

/home/eserv/run_bullseye_stage1.py $1
source /home/eserv/splunk/bin/setSplunkEnv
cd /home/eserv/perforce/splunk/current/new_test
source /home/eserv/perforce/splunk/current/new_test/setTestEnv
/home/eserv/run_bullseye_stage2.py $1
# After run Bullseye, copy over the coverage files to esnas
# and them clean the /usr/local/bullseye_reports directory
cp -r --remove-destination /home/eserv/bullseye_reports/* /mnt/bullseye_report_new
#rm -rf /home/eserv/bullseye_reports/*

# We also want to clean up SPLUNK_HOME, and source
#rm -rf /home/eserv/splunk/current/*
#rm -rf /home/eserv/perforce/splunk/*
#source /home/eserv/.bash_profile
