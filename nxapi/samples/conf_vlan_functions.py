import requests
import json


my_headers = {'content-type': 'application/json-rpc'}
username = "admin"
password = "ciscotme"

def configure_vlan(ip, vlanId):
    url = "http://"+ip+"/ins"
    
    payload=[
      {"jsonrpc": "2.0","method": "cli","params": {"cmd": "conf t","version": 1},"id": 1},
      {"jsonrpc": "2.0","method": "cli","params": {"cmd": "vlan "+vlanId,"version": 1},"id": 2},
      {"jsonrpc": "2.0","method": "cli","params": {"cmd": "exit","version": 1},"id": 3}
    ]

    response = requests.post(url,data=json.dumps(payload), headers=my_headers,auth=(username,password)).json()


def print_vlans(ip):
    url = "http://"+ip+"/ins"
    vlans = []
    payload=[{"jsonrpc": "2.0",
          "method": "cli",
          "params": {"cmd": "show vlan brief",
                     "version": 1},
          "id": 1}
         ]
    response = requests.post(url, data=json.dumps(payload), headers=my_headers, auth=(username, password)).json()
    vlan_table = response['result']['body']['TABLE_vlanbriefxbrief']['ROW_vlanbriefxbrief']
    print ("\n"+"="* 35)
    print "printing configured vlans on %s"%ip
    for iter in vlan_table:
        print iter["vlanshowbr-vlanid-utf"],
    print ("\n"+"="*35)
    
def main():
    print "enter ip address"
    ip=raw_input()
    print_vlans(ip)

    y_n = raw_input("\n Do you want to add a vlan ? (y/n)")

    while(y_n == 'y'):    
        vlanId=raw_input("Enter vlan to be configured : ")
        configure_vlan(ip,vlanId)
        print_vlans(ip)
        y_n = raw_input("\n Do you want to add another vlan ? (y/n)")

    print " End of vlan script"
    
if __name__ == "__main__":
    main()
 
