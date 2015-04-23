import requests
import json

print "enter ip address"
ip=raw_input()

print "enter vlan to be configured"
vlanId=raw_input()

myheaders = {'content-type': 'application/json-rpc'}
url = "http://"+ip+"/ins"
username = "admin"
password = "ciscotme"


payload=[
  {"jsonrpc": "2.0","method": "cli","params": {"cmd": "conf t","version": 1},"id": 1},
  {"jsonrpc": "2.0","method": "cli","params": {"cmd": "vlan "+vlanId,"version": 1},"id": 2},
  {"jsonrpc": "2.0","method": "cli","params": {"cmd": "exit","version": 1},"id": 3}
]

response = requests.post(url,data=json.dumps(payload), headers=myheaders,auth=(username,password)).json()



