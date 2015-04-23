#!/usr/bin/env python
#
# Copyright (C) 2014 Cisco Systems Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# The following script check if vlans are consistant across different switches.
# If not, then this script will insert the missing vlans

import sys
import json
import requests
import ast
from string import Template


my_headers = {'content-type': 'application/json-rpc'}


switch = [
          ['172.26.246.144', 'admin', 'xyz'],
          ['172.26.246.145', 'admin', 'xyz'],
          ['172.26.246.146', 'admin', 'xyz'],
          ['172.26.246.148', 'admin', 'xyz'],
         ]

required_vlans = [10,
                  11,
                  12,
                  13,
                  17,
                  22,
                  23,
                  24,
                  25,
                  26,
                  27,
                  28,
                  30,
                  31,
                  32,
                  33,
                  34,
                  35]

#######################################
req_vlans_sort = required_vlans.sort()
jsonrpc_template = Template("{'jsonrpc': '2.0', 'method': '$method', 'params': ['$params', 1], 'id': '$jrpc_id'}")


#conf_vlan_payload = 
def check_vlan_consistancy(row):
        vlans = []
        switch_ip = row[0]
        username = row[1]
        password = row[2]

        payload = [{'jsonrpc': '2.0', 'method': 'cli', 'params': ['show vlan',1], 'id': '1'}]
        my_data = json.dumps(payload)
        
        url = "http://"+switch_ip+"/ins"
        response = requests.post(url, data=my_data, headers=my_headers, auth=(username, password))

        #parse information of show vlan    
        vlan_table = response.json()['result']['body']['TABLE_mtuinfo']['ROW_mtuinfo']
        for iter in vlan_table:
            vlans.append(int(iter['vlanshowinfo-vlanid']))

        vlans.sort()

        missing_vlans = list(set(required_vlans)-set(vlans))
        if (vlans != required_vlans) and (missing_vlans != []):
            
            print "switch: "+switch_ip+" is missing_vlans: "+str(sorted(missing_vlans))
            config_vlans(row, missing_vlans)
        elif (missing_vlans == []):
            print"switch: "+switch_ip+" is NOT missing any of the required vlans"
        else:
            return 1

def config_vlans(row, missing_vlans):   

    switch_ip = row[0]
    username = row[1]
    password = row[2]

    print "Configuring On Switch:  "+switch_ip+" the following vlans  "+str(sorted(missing_vlans))

    url = "http://"+switch_ip+"/ins"
    
    batch_cmd = "["
    id_counter = 1
    
    command = "conf t"
    batch_cmd = batch_cmd + jsonrpc_template.substitute(params=command, jrpc_id=id_counter, method='cli')
    
    for v in missing_vlans:
        batch_cmd += ','
        command = 'vlan ' + str(v)
        id_counter += 1
        batch_cmd = batch_cmd + jsonrpc_template.substitute(params=command, jrpc_id=id_counter, method='cli')

    batch_cmd = batch_cmd + "]"
    my_data = json.dumps(ast.literal_eval(batch_cmd))

    response = requests.post(url, data=my_data, headers=my_headers, auth=(username, password))
    #print (response.text)
                                               
def main():
    print "**** Calling vlan consistency checker ***" 
    for row in switch:    
        consistant = check_vlan_consistancy(row)

    print "*** Vlan consistency checker complete ***"
if __name__ == "__main__":
    main()
 
