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
# Description:  Simple script to configure an ACL via JSONRPC,
#               Checks to make sure it was configured
#               Unconfigures the same ACL,
#               And checks to make sure it is unconfigured

import requests
import json
    
    

# Send our message to switch via HTTP post and return response
def send_msg(jsonrpc):
    url = "http://172.25.91.147/ins"
    my_headers = {'content-type': 'application/json-rpc'}
    uname = "admin"
    password = "ciscotme"

    response = requests.post(url, data=jsonrpc, headers=my_headers, auth=(uname, password))
    return response


# Create a JSON-RPC request from a given param/id
# If id is null we will create a notification
def create_request(params, jrpc_id):
    req = {
        "jsonrpc": "2.0",
        "method": "cli",
        "params": [params, 1]
    }
    if jrpc_id != None:
	req["id"] = jrpc_id
    return req


# Try to find the "acl_name". If we find it print out the name
# show acl will return emtpy result if there is no ACL
def verify_acl_config(json, acl_name):
    if json.has_key("result"):
	result = json.get("result")
	if result == None:
	    print("ACL " + acl_name + " is not configured")
	else:
	    try:
		found_acl = result['body']['TABLE_ip_ipv6_mac']['ROW_ip_ipv6_mac']['acl_name']
		if found_acl == acl_name:
		    print("ACL " + acl_name + " was configured")
	    except TypeError:
		print("Unexpected JSON output")


# Test program to configure a ACL and verify, 
#Then disable the ACL and verify again
def main():

    acl_name = "acl-1"
    allow_ip = "192.168.2.0/24"
    
    print("Enabling ACL " + acl_name)

    # Create batch command to configure ACL
    enable_acl_cmd = [create_request("ip access-list " + acl_name, None),
	          create_request("permit ip " + allow_ip + " any", None),
		  create_request("statistics", None)]

    # status code must be 204 for notification success
    rsp = send_msg(json.dumps(enable_acl_cmd))
    if rsp.status_code != 204:
	print("Server failed to handle request");

    # Verify that ACL went through, status must be 200 for non-notification success
    verify_acl_cmd = create_request("show ip access-lists " + acl_name, 1)
    rsp = send_msg(json.dumps(verify_acl_cmd))
    if rsp.status_code == 200:
	verify_acl_config(rsp.json(), acl_name)
    else:
	print("Error HTTP code : ", rsp.status_code)

    print("Disabling ACL " + acl_name)

    # Create cmd to disable ACL
    disable_acl_cmd = create_request("no ip access-list " + acl_name, None)
    rsp = send_msg(json.dumps(disable_acl_cmd))
    if rsp.status_code != 204:
	print("Server failed to handle request");

    # Verify that ACL is no longer there
    rsp = send_msg(json.dumps(verify_acl_cmd))
    if rsp.status_code == 200:
	verify_acl_config(rsp.json(), acl_name)
    else:
	print("Error HTTP code : ", rsp.status_code)


if __name__ == "__main__":
    main()
