import os
import json
import copy
import pycurl
from io import BytesIO
from io import StringIO
from cryptography.fernet import Fernet
from jsondiff import diff, symbols

import NotionTools as nt

def areEdgesHealthOK(edges):

    all_ok = True

    for edge in edges:
        if ( False == isEdgeHealthOK(edge) ):
            all_ok = False

    return all_ok

def queryEdge(edge, API_CMD, post_fields=''):

    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, 'https://' + edge['Internet IP'] + API_CMD)
    c.setopt(c.SSL_VERIFYPEER, 0)
    c.setopt(c.SSL_VERIFYHOST, 0)
    c.setopt(c.VERBOSE, 0)
    c.setopt(c.TIMEOUT_MS, 10000)
    c.setopt(c.USERNAME, edge['API Username'])
    c.setopt(c.HTTPHEADER, ['Content-Type: application/json'])
    c.setopt(c.PASSWORD, edge['API Password'])
    if post_fields:
        c.setopt(c.POSTFIELDS, post_fields)
    c.setopt(c.WRITEDATA, buffer)
    try:
        json_response = {}
        c.perform()
    except Exception as e:
        print(f"pycurl error: {e}")

    else:
        response_code = c.getinfo(pycurl.RESPONSE_CODE)
        if response_code in {200,201}:
            json_response = json.loads(buffer.getvalue())
        else:
            print("response code: " + str(response_code))
            print('https://' + edge['Internet IP'] + API_CMD)
            json_response = {}
            json_error_message = json.loads(buffer.getvalue())
            print(json_error_message)

    finally:
        c.close()

    return json_response

def doLondonPathsExist(edge):

    post_fields = json.dumps({
        'run': {
            'destination_isd_as': '65-2:0:6c'
            }})

    API_CMD = '/api/v1/tools/scion/showpaths'
    response = queryEdge(edge, API_CMD, post_fields)

    if (len(response['paths']) > 0):
        return True
    return False

def isEdgeHealthOK(edge):

    print("Checking: " + edge.get('Name'))

    API_CMD = '/api/v1/health'
    post_fields = ''
    response = queryEdge(edge, API_CMD, post_fields)


    fail_count = 0
    
    for check in response['health']['checks']:
        if not (check.get("status").lower() in ['passing', 'notice']):
            fail_count += 1
            #print(check)

    print("Check failed: " + edge.get('Name') + " " + str(fail_count))

    return True if fail_count == 0 else False

def getEdgeConfig(edge):
    post_fields=''
    API_CMD = '/api/v1/configs/latest'
    return queryEdge(edge, API_CMD, post_fields)

def putEdgeConfig(edge, config):
    post_fields=json.dumps(config)
    API_CMD = '/api/v1/configs'
    return queryEdge(edge, API_CMD, post_fields)

def updateBGPConfig(new_config, edge, assigned_nodes):

    BGP_DEFAULT_AS = 65001
    BGP_PEER_AS = 65002

    new_config["config"]["bgp"] = {
            "global": {
                "as": BGP_DEFAULT_AS,
                "router_id": edge.get("Internet IP"),
            }
            }

    if assigned_nodes:
        new_config["config"]["bgp"]["neighbors"] = []
    for node in assigned_nodes:
        new_config["config"]["bgp"]["neighbors"].append(
                {
                "enabled": True,
                "neighbor_address": node.get("Local GRE IP"),
                "peer_as": BGP_PEER_AS
                })
    return new_config

def updateFirewallConfig(new_config, edge):

    new_config["config"]["firewall"] = {}
    return new_config

def updateGREConfig(new_config, edge, assigned_nodes):
    if (assigned_nodes):
        new_config["config"]["interfaces"]["gres"] = []
        sequence_id=0
        for node in assigned_nodes:
            sequence_id+=10
            new_config["config"]["interfaces"]["gres"].append({
                "addresses": [
                    node.get("Remote GRE IP") + "/31",
                    ],
                "destination": node.get("Local Tunnel IP"),
                "name": "gre" + node.get("Edge GRE ID"),
                "routes": [
                {
                    "comment": node.get("Name"),
                    "metric": 10,
                    "sequence_id": sequence_id,
                    "to": node.get("Service IP") + "/32",
                    "via": node.get("Local GRE IP")
                }
                ],
            "source": edge["VPP IP"]
            })
    return new_config

def updateStaticAnnouncementsConfig(new_config, edge, assigned_nodes, edges):

    if 1 == len(edges):
        new_config["config"].pop("scion_tunneling", None)
        return

    new_config["config"]["scion_tunneling"] = {
            "domains": [],
            "remotes": [],
            "endpoint": {
                "control_port": 40201,
                "data_port": 40200,
                "enabled": True,
                "ip": edge["VPP IP"],
                "probe_port": 40202
            },
            "path_filters": [{
                "name": "allow_all",
                "description": "Allow all paths",
                "acl": ["+ 0"]
            }],
            "traffic_matchers": [{
                "condition": "BOOL=true",
                "name": "default"
            }]
            }

    sequence_id = 0
    if assigned_nodes:
        new_config["config"]["scion_tunneling"]["static_announcements"] = []
    for node in assigned_nodes:
        new_config["config"]["scion_tunneling"]["static_announcements"].append({
            "description": node.get("Name"),
            "next_hop_tracking": {
                "target": node.get("Local GRE IP")
            },
            "prefixes": [
                node.get("Service IP") + "/32"
            ],
            "sequence_id": sequence_id
        })
        sequence_id += 1

    domains = new_config["config"]["scion_tunneling"]["domains"]
    remotes = new_config["config"]["scion_tunneling"]["remotes"]

    for edge_itr in edges:
        if edge_itr["Name"] == edge["Name"]:
            continue

        remotes.append({
            "isd_as": edge_itr["ISD-AS"]
        })

        prefixes = []
        assigned_nodes = nt.getAssignedNodes(edge_itr)
        if not assigned_nodes:
            continue
        for node in assigned_nodes:
            prefixes.append(node["Service IP"]+"/32")

        domains.append({
                "default": False,
                "description": edge_itr["Name"],
                "name": edge_itr["ISD-AS"],
                "prefixes": {
                    "accept_filter": [
                        {
                            "action": "ACCEPT",
                            "prefixes": prefixes,
                            "sequence_id": 0
                        }
                     ],
                     "announce_filter": [
                         {
                           "action": "ACCEPT",
                           "prefixes": [
                               "0.0.0.0/0"
                           ],
                           "sequence_id": 0
                         }
                      ]
                 },
                 "remote_isd_ases": [
                 {
                     "action": "ACCEPT",
                     "isd_as": edge_itr["ISD-AS"],
                     "sequence_id": 0
                 }
                 ],
                 "traffic_policies": [
                 {
                      "failover_sequence": [
                          {
                              "path_filter": "allow_all",
                              "sequence_id": 0
                          }
                       ],
                      "sequence_id": 0,
                      "traffic_matcher": "default"
                 }
                 ]
               })

    return new_config

def updateEdgeConfig(edge, edges):
    print("checking edge: " + edge["Name"] + " (" + edge["Internet IP"] + ")...")

    running_config = getEdgeConfig(edge)
    if not running_config:
        print("no running config - skipping " + edge["Name"] + " (" + edge["Internet IP"] + ")...")
    else:

        new_config = copy.deepcopy(running_config)

        assigned_nodes = nt.getAssignedNodes(edge)

        updateBGPConfig(new_config, edge, assigned_nodes)
    
        updateFirewallConfig(new_config, edge)
    
        updateGREConfig(new_config, edge, assigned_nodes)
    
        updateStaticAnnouncementsConfig(new_config, edge, assigned_nodes, edges)
    
        with open(edge["Name"]+"-new-config.json", "w") as new_config_file:
            json.dump(new_config, new_config_file, indent=4)
    
        differences = diff(running_config, new_config)
    
        if differences:
            print("Changes required for this edge. Savings differences locally and pushing up to the Edge.")
            with open(edge["Name"]+"-running-config.json", "w") as running_config_file:
                json.dump(running_config, running_config_file, indent=4)
                putEdgeConfig(edge,new_config)
        else:
            print("No changes required to this Edge.")

    return

def checkAllEdgesHealth():

    print("Reading list of Edges from Notion...")
    edges = nt.getAllAutoConfigEdges()
    print("done. ")
    print("There are " + str(len(edges)) + " Edges set to AutoConfig in Notion.")
    print("")

    areEdgesHealthOK(edges)

    return

checkAllEdgesHealth()

