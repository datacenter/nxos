import sys
import json
import requests
import ast
import logging

from string import Template

vlan_threshold = 20

my_headers = {'content-type': 'application/json-rpc'}


switch = [['10.126.216.30', 'admin', 'password'],
          ['10.126.216.21', 'admin', 'password'],
         ]

jsonrpc_template = Template("{'jsonrpc': '2.0', 'method': '$method', 'params': ['$params', 1], 'id': '$jrpc_id'}")
logging.basicConfig(filename='vlan_scale_check.log',level = logging.ERROR, format = '%(asctime)s %(name)-5s %(message)s',
                    datefmt = '%m-%d %H:%M',filemode ='a')
logging.critical('===================================')
logging.critical('Ran vlan_scale_checker')
logging.getLogger('test')
 
def vlan_scale(row):
        vlans = []
        switch_ip = row[0]
        username = row[1]
        password = row[2]

        payload = [{'jsonrpc': '2.0', 'method': 'cli', 'params': ['show vlan summary',1], 'id': '1'}]
        my_data = json.dumps(payload)
        
        url = "http://"+switch_ip+"/ins"
        response = requests.post(url, data=my_data, headers=my_headers, auth=(username, password))
        
        #parse information of show vlan    
        vlansum = response.json()['result']['body']['vlansum-all-vlan']

        if int(vlansum) > int(vlan_threshold):
            create_syslog(row, vlansum);
        else:
            print "Vlan scale NOT exceeded on switch:"+str(switch_ip)
            logging.critical("Vlan scale NOT exceeded on switch:"+str(switch_ip))
def create_syslog(row, vlansum):   

    #extract switch info
    switch_ip = row[0]
    username = row[1]
    password = row[2]
    
    message_str = "Vlan scale limit exceeded on switch: "+str(switch_ip)+\
    ". Found vlans = "+str(vlansum)+", Threshold vlans = "+str(vlan_threshold)
    print message_str

    logging.critical(message_str)

    # Now use On-board Python to create a syslog from the device 
    url = "http://"+switch_ip+"/ins"
    
    batch_cmd = "["
    id_counter = 1
 
    #create a syslog on the nexus device   
    command = 'python'
    batch_cmd = batch_cmd + jsonrpc_template.substitute(params=command, jrpc_id=id_counter, method='cli')
    

    batch_cmd += ','
    command = 'import syslog'
    id_counter += 1
    batch_cmd = batch_cmd + jsonrpc_template.substitute(params=command, jrpc_id=id_counter, method='cli')

    
    batch_cmd += ','
    syslog_msg = "Vlan scale limit exceeded. Found vlan = "+str(vlansum)+", Threshold vlan = "+str(vlan_threshold)
    command = 'syslog.syslog(3,"+'+syslog_msg+'")'
    id_counter += 1
    batch_cmd = batch_cmd + jsonrpc_template.substitute(params=command, jrpc_id=id_counter, method='cli')
    
    batch_cmd += ','   
    command = 'exit'
    id_counter += 1
    batch_cmd = batch_cmd + jsonrpc_template.substitute(params=command, jrpc_id=id_counter, method='cli')

    
    batch_cmd = batch_cmd + "]"
    my_data = json.dumps(ast.literal_eval(batch_cmd))
    response = requests.post(url, data=my_data, headers=my_headers, auth=(username, password))



def main():
    
    for row in switch:    
        vlan_check = vlan_scale(row)

if __name__ == "__main__":
    main()
