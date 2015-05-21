#!/usr/bin/env python
#
# Copyright (C) 2015 Cisco Systems Inc.
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
# The following script check if the VPCs configured on the switch pair are up.
# If they are down, it will check for any configuration inconsistency and try to correct them.
# 
# Currently the correction is for MTU mismatch. This can be extended to other inconsistency types
#


import sys
import json
import requests
import ast
from string import Template
import time


my_headers = {'content-type': 'application/json-rpc'}

## TODO Specify the Mgmt IP and the credentials here

switch_a =  { 'mgmt_ip' : '10.104.251.85', 'username': 'admin', 'user_pw' : 'password'}
switch_b =  { 'mgmt_ip' : '10.104.251.86', 'username': 'admin', 'user_pw' : 'password'}
vpc_id = []


#######################################
jsonrpc_template = Template("{'jsonrpc': '2.0', 'method': '$method', 'params': ['$params', 1], 'id': '$jrpc_id'}")

#######################################

type_tbl = {
	'Interface type' : '1',
	'LACP Mode'		 : '1',
	'STP Port Guard' : '1',   
	'STP Port Type'	: '1',
	'Speed'              : '1',
	'Duplex'             : '1',
	'MTU'              : '1',
	'Port Mode'       : '1',
	'STP MST Simulate PVST' : '1',
	'Native Vlan'       : '1',
	'Pvlan list'       : '2',
	'Admin port mode' : '1',
	'lag-id' : '1',
	'mode' : '1',
	'vPC card type'     : '1',
	'Allowed VLANs'      : '-',
	'Local error VLANs' : '-'
}   


def check_vpc_status(switch_x):
    
	switch_ip = switch_x["mgmt_ip"]	
	switchuser = switch_x["username"]
	switchpassword = switch_x["user_pw"]
	return_data = {}
	url = "http://"+switch_ip+"/ins"

	myheaders={'content-type':'application/json-rpc'}
	payload=[
	  {
	    "jsonrpc": "2.0",
	    "method": "cli",
	    "params": {
	      "cmd": "show vpc brief",
	      "version": 1.2
	    },
	    "id": 1
	  }
	]

	response = requests.post(url,data=json.dumps(payload), headers=myheaders,auth=(switchuser,switchpassword)).json()



	resp_body = response['result']['body']
	return_data['vpc-peer-status'] = resp_body['vpc-peer-status']
	resp_vpc_table = resp_body['TABLE_vpc']['ROW_vpc']


	for iter in resp_vpc_table:

		one_vpc_id = iter['vpc-id']
		vpc_id.append(one_vpc_id)

		return_data[str(one_vpc_id)] = {}
		return_data[str(one_vpc_id)]['consistency-status'] = iter['vpc-consistency-status']
		return_data[str(one_vpc_id)]['port-id'] = iter['vpc-ifindex']
	
	return return_data


def check_vpc_consistency(switch_x,switch_y, vpc_id):
	
	# print "VPC : " + str(vpc_id)

	cmd = "show vpc consistency-parameters vpc " + str(vpc_id) + " errors"
	switch_ip = switch_x["mgmt_ip"]	
	switchuser = switch_x["username"]
	switchpassword = switch_x["user_pw"]
	return_data = {}
	url = "http://"+switch_ip+"/ins"

	myheaders={'content-type':'application/json-rpc'}

	payload=[
	  {
	    "jsonrpc": "2.0",
	    "method": "cli",
	    "params": {
	      "cmd": cmd,
	      "version": 1.2
	    },
	    "id": 1
	  }
	]

	# print payload 
	response = requests.post(url,data=json.dumps(payload), headers=myheaders,auth=(switchuser,switchpassword)).json()

	resp_body = response['result']['body']['TABLE_vpc_consistency']['ROW_vpc_consistency']
	fail_list = []

	for iter in resp_body:
		i_name = iter['vpc-param-name']
		i_type = iter['vpc-param-type']
		i_local = iter['vpc-param-local-val']
		i_peer = iter['vpc-param-peer-val']

		if i_local != i_peer:
			print "Found Inconsistency in " + i_name + ": local val: " + i_local + " peer val : " + i_peer
			fail_list.append(iter)

	# print fail_list

	return fail_list

def correct_vpc_consistency(switch_x, switch_y,fail_list, vpc_id,port_id):


	print "Correcting VPC " + str(vpc_id) + "\n"

	# print fail_list
	switch_ip = ""
	switchuser = ""
	switchpassword = ""


	for iter in fail_list:
		if iter['vpc-param-name'] == "MTU":
			print "Correcting MTU"
			higher_mtu = ""
			if iter['vpc-param-local-val'] < iter['vpc-param-peer-val']:
				higher_mtu = iter["vpc-param-peer-val"]
				switch_ip = switch_x["mgmt_ip"]	
				switchuser = switch_x["username"]
				switchpassword = switch_x["user_pw"]
			else:
				higher_mtu = iter["vpc-param-local-val"]
				switch_ip = switch_y["mgmt_ip"]	
				switchuser = switch_y["username"]
				switchpassword = switch_y["user_pw"]

		payload=[
		  {
		    "jsonrpc": "2.0",
		    "method": "cli",
		    "params": {
		      "cmd": "conf t",
		      "version": 1.2
		    },
		    "id": 1
		  },
		  {
		    "jsonrpc": "2.0",
		    "method": "cli",
		    "params": {
		      "cmd": "interface " + port_id,
		      "version": 1.2
		    },
		    "id": 2
		  },
		  {
		    "jsonrpc": "2.0",
		    "method": "cli",
		    "params": {
		      "cmd": "mtu " + str(higher_mtu),
		      "version": 1.2
		    },
		    "id": 3
		  }
		]

		url = "http://"+switch_ip+"/ins"
		myheaders={'content-type':'application/json-rpc'}
		# print "Payload:"
		# print payload
		# print url
		# print higher_mtu
		response = requests.post(url,data=json.dumps(payload), headers=myheaders,auth=(switchuser,switchpassword)).json()

		# print response



                                              
def main():

	print "**** Calling vlan consistency checker ***" 
	consistent1 = check_vpc_status(switch_a)

	print "Checking VPC status. Results:\n "
	is_consistent = 1

	for one_vpc_id in vpc_id:
		# print str(one_vpc_id)
		# print consistent1[str(one_vpc_id)] ['consistency-status']
		if consistent1[str(one_vpc_id)]['consistency-status'] == "INVALID":
			is_consistent = 0
			print "VPC " + str(one_vpc_id) + " is inconsistent - checking reason...\n"
			cons_check = check_vpc_consistency(switch_a, switch_b, one_vpc_id)
			#print "cons_check "
			#print cons_check
			correct_it = correct_vpc_consistency(switch_a, switch_b,cons_check, one_vpc_id,consistent1[str(one_vpc_id)]['port-id'] )
			print "VPC" + str(one_vpc_id) + " corrected"


	time.sleep(5)

	if is_consistent == 0:
		print "Rechecking VPC Status after correction. Results: \n"
		consistent_recheck = check_vpc_status(switch_a)

		for one_vpc_id in vpc_id:
			# print str(one_vpc_id)
			# print consistent_recheck[str(one_vpc_id)] ['consistency-status']
			if consistent_recheck[str(one_vpc_id)]['consistency-status'] == "INVALID":
				print "VPC " + str(one_vpc_id) + " is still inconsistent"
	else:
		print "No Inconsistency found !! \n"



	print "*** Vlan consistency checker complete ***"
if __name__ == "__main__":
	main()
 