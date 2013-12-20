import os
import logging
import time
import pytest
LOGGER = logging.getLogger('tests.clustering.framework')


@pytest.fixture(scope="class")
def cluster(request):
    '''
    '''
    from splunktest.framework.FrameworkTest import Cluster
    cluster = Cluster(masters=1, slaves=3, search_heads=1, hosts=pytest.config.hosts)
    def fin():
        '''
        '''
        cluster.teardown()
    request.addfinalizer(fin)
    return cluster

@pytest.fixture(scope="class")
def empty_cluster(request):
    '''
    '''
    from splunktest.framework.FrameworkTest import Cluster
    cluster = Cluster(masters=1, slaves=1, search_heads=0, hosts=pytest.config.hosts)
    def fin():
        '''
        '''
        cluster.teardown()
    request.addfinalizer(fin)
    return cluster

@pytest.fixture(scope="class")
def multisite_cluster(request):
    '''
    '''
    from splunktest.framework.FrameworkTest import Cluster
    cluster = Cluster(hosts=pytest.config.hosts, multisite=True, sites=2)
    def fin():
        '''
        '''
        cluster.teardown()
    request.addfinalizer(fin)
    return cluster

@pytest.fixture(scope="class")
def forwarder(request, cluster):
    '''
    '''
    cluster.forwarder.configure(cluster.slaves)
    cluster.forwarder.forward_data()
    search_head = cluster.search_heads[0]
    search_head.indexes()['main'].wait_for_event_count(ecount=250000, timeout=120)


def apply_bundle(cluster):
    '''
    '''
    auth_str = '-auth %s:%s' %(pytest.config.username, pytest.config.new_password)
    output = cluster.master.execute('apply cluster-bundle --answer-yes %s' %auth_str)
    assert output[0] == 0

    tries = 20
    time_to_wait = 10
    for aTry in range(tries):
        output1 = cluster.master.execute('show cluster-bundle-status %s' %auth_str)
        LOGGER.info("output1: %s" % output1[1])
        time.sleep(time_to_wait)
        output2 = cluster.master.execute('show cluster-bundle-status %s' %auth_str)
        LOGGER.info("output2: %s" % output2[1])
        if output1[1] == output2[1]:
            break
        else:
            time.sleep(time_to_wait)
    assert output1[1] == output2[1]

def update_master_conf(master, conf_file, stanza, attribute_value_pairs):
    path_to_config_bundle = os.path.join(master.splunk_home, 'etc', 'master-apps', '_cluster', 'local', conf_file)

    stanza_str = '['+stanza+']'
    attribute_str = attribute_value_pairs.keys()[0]
    attribute_value_str= attribute_value_pairs[attribute_str]
    if(master.is_remote == True):

	#Note: For windows remote VMS, i assume helmut can ssh into windows VM <if we make helmut work on windows>. If thats the case, cat & pipe will be automatically availabe in cmd prompt.. Have seen windows cmds with basic linux commands working..

        #deleting existing conf-file
        os.system(" ssh " + CONFIG.ssh_user + "@" + master.host_name + " 'rm " + path_to_config_bundle)

        #command for writing stanza to remote conf-file
        ssh_stanza_string =  "echo "+ "'" +stanza_str +"'" + " | " + " ssh " + CONFIG.ssh_user + "@" + master.host_name + " '" +" cat >> " + path_to_config_bundle + "'"
        LOGGER.info("Running command to add stanza to conf on remote master. Command: " + ssh_stanza_string)

        os.system(ssh_stanza_string)

        LOGGER.info("Done adding  stanza: "+stanza_str)

        LOGGER.info("Adding attribute=value pairs to conf on remote master under the stanza: "+stanza_str)

        for key, value in attribute_value_pairs:
            #command for writing attribute = value to remote conf-file 
            ssh_keyvalue_string = "echo " + "'" + attribute_str + "=" + attribute_value_str + "'" + " | " + " ssh " + CONFIG.ssh_user + "@" + master.host_name + " '" +" cat >> " + path_to_config_bundle + "'"

            LOGGER.info("Running command: " + ssh_keyvalue_string)
            os.system(ssh_keyvalue_string)
        LOGGER.info("Done updating conf file on remote master.")

    else:
        # doing above things locally
        if(os.path.exists(path_to_config_bundle)):
            os.remove(path_to_config_bundle)
        f=open((path_to_config_bundle), 'w')
        f.write(stanza_str + '\n')
        for key, value in attribute_value_pairs.items():
            f.write(key + '=' + value + '\n')
        f.close()
	#taking below logic out as it won't run on windows even in stanalone mode..
        #stanza_string = "echo " + "'" +stanza_str +"'" + " | " +" cat >> " + path_to_config_bundle
        #keyvalue_string = "echo " + "'" + attribute_str + "=" + attribute_value_str + "'" + " | " + " cat >> " + path_to_config_bundle
        #LOGGER.info("Running command to update conf on local master. Command: " + stanza_string)
        #os.system(stanza_string)
        #LOGGER.info("Running command to update conf on local master. Command: " + keyvalue_string)
        #os.system(keyvalue_string)
