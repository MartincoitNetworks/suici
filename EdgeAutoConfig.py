import os
import json
import copy
import pycurl
from io import BytesIO
from io import StringIO

NODE_NOTION_DATA_SOURCE_ID='28266302-4cb3-8014-a174-000b4ad84140'
EDGE_NOTION_DATA_SOURCE_ID = '27f66302-4cb3-80fb-bec3-000bc8d31c19'

def getNotionAPIKey():

    try:
        NOTION_API_KEY=os.environ['NOTION_API_KEY']
    except KeyError as e:
        print(f"")
        print(f"KeyError: {e} - NOTION_API_KEY environment variable is not set.")
        print(f"")
        raise

    return NOTION_API_KEY


def getAllNodes():

    NOTION_API_KEY = getNotionAPIKey()

    nodes = []

    for result in queryNotion(NODE_NOTION_DATA_SOURCE_ID):
        nodes.append(buildNodeFromNotionJSON(result))

    return nodes

def getAssignedNodes(edge):

    nodes = []

    post_fields = json.dumps({
            "filter": {
                "property": "Assigned Edge",
                "relation": {
                    "contains": edge["id"]
                }
                }
            })

    for result in queryNotion(NODE_NOTION_DATA_SOURCE_ID,post_fields):
        nodes.append(buildNodeFromNotionJSON(result))

    return nodes


def getAllAutoConfigEdges():

  edges = []

  post_fields = json.dumps(
  {
  "filter": {
    "property": "Auto Config",
    "checkbox": {
      "equals": True
    }
  }
  })

  results = queryNotion(EDGE_NOTION_DATA_SOURCE_ID, post_fields)

  for result in results:
    edges.append(getEdgeFromNotionJSON(result))

  return edges

      


def areEdgesHealthOK(edges, password='probably_not_a_secret'):
  for edge in edges:
    status = isEdgeHealthOK(edge, password)
    if (False == status):
        return False
  return True

def queryEdge(IP, password, API_CMD, post_fields=''):

  buffer = BytesIO()
  c = pycurl.Curl()
  c.setopt(c.URL, 'https://' + IP + API_CMD)
  c.setopt(c.SSL_VERIFYPEER, 0)
  c.setopt(c.SSL_VERIFYHOST, 0)
  c.setopt(c.VERBOSE, 0)
  c.setopt(c.TIMEOUT_MS, 5000)
  c.setopt(c.USERNAME, 'admin')
  c.setopt(c.HTTPHEADER, ['Content-Type: application/json'])
  c.setopt(c.PASSWORD, password)
  if post_fields:
    c.setopt(c.POSTFIELDS, post_fields)
  c.setopt(c.WRITEDATA, buffer)
  c.perform()
#  print(c.getinfo(pycurl.RESPONSE_CODE))
  c.close()

  return json.loads(buffer.getvalue())

def doLondonPathsExist(edge, password='probably_not_a_secret'):

  post_fields = json.dumps({
  'run': {
    'destination_isd_as': '65-2:0:6c'
   }})

  API_CMD = '/api/v1/tools/scion/showpaths'

  response = queryEdge(edge.get('Internet IP'), password, API_CMD, post_fields)

  if (len(response['paths']) > 0):
      return True
  return False

def isEdgeHealthOK(edge, password='probably_not_a_secret'):

  API_CMD = '/api/v1/health'
  post_fields = ''
  response = queryEdge(edge.get('Internet IP'), password, API_CMD, post_fields)
    
  for check in response['health']['checks']:
      if not (check.get("status").lower() in ['passing', 'notice']):
          return False
  return True

def buildNodeFromNotionJSON(response):
    node = {
            "id": response['id'],
            "Name": response['properties']['Name']['title'][0]['text']['content'],
            "Edge GRE ID": str(response['properties']['Edge GRE ID']['number']),
            "Edge Internet IP": response['properties']['Edge Internet IP']['rollup']['array'][0]['rich_text'][0]['plain_text'],
            "Local Tunnel IP": response['properties']['Local Tunnel IP']['rich_text'][0]['text']['content'],
            "Remote Tunnel IP": response['properties']['Remote Tunnel IP']['formula']['string'],
            "Service IP": response['properties']['Service IP']['rich_text'][0]['text']['content'],
            "Assigned Edge Name": response['properties']['Assigned Edge Name']['rollup']['array'][0]['title'][0]['plain_text'],
            "Assigned ISD-AS": response['properties']['Assigned ISD-AS']['rollup']['array'][0]['rich_text'][0]['text']['content'],
            'Local GRE IP': response['properties']['Local GRE IP']['formula']['string'],
            'Remote GRE IP': response['properties']['Remote GRE IP']['formula']['string']
    }
    return node

def getEdgeFromNotionJSON(response):
    edge = {
            "id": response['id'],
            "Name": response['properties']['Name']['title'][0]['text']['content'],
            "Internet IP": response['properties']['Internet IP']['rich_text'][0]['text']['content'],
            "VPP IP": response['properties']['VPP IP']['rich_text'][0]['text']['content'],
            "ISD-AS": response['properties']['ISD-AS']['rich_text'][0]['text']['content']
    }
    return edge



def queryNotion(data_source_id, post_fields=''):

  NOTION_API_KEY = getNotionAPIKey()

  buffer = BytesIO()
  c = pycurl.Curl()
  c.setopt(c.URL, 'https://api.notion.com/v1/data_sources/' + data_source_id + '/query')
  c.setopt(c.HTTPHEADER, ['Authorization: Bearer ' + NOTION_API_KEY,
                          'Notion-Version: 2025-09-03',
                          'Content-Type: application/json'])
  c.setopt(c.POST, 1)
  c.setopt(c.POSTFIELDS, post_fields )
  c.setopt(c.WRITEDATA, buffer)
  c.setopt(c.TIMEOUT_MS, 5000)
  c.perform()
  c.close()

  return json.loads(buffer.getvalue())['results']


def findEdgeByName(name):

  NOTION_API_KEY = getNotionAPIKey()

  edges = []

  post_fields = json.dumps(
  {
  "filter": {
    "property": "Name",
    "title": {
      "contains": name
    }
  }
  })

  edge_data_source_id = '27f66302-4cb3-80fb-bec3-000bc8d31c19'
  results = queryNotion(edge_data_source_id, post_fields)

  for result in results:
      edges.append(getEdgeFromNotionJSON(result))

  return edges

def getEdgeConfig(edge, password='probably_not_a_secret'):
    IP=edge.get('Internet IP')
    post_fields=''
    API_CMD = '/api/v1/configs/latest'
    return queryEdge(IP, password, API_CMD, post_fields)

def putEdgeConfig(edge, config, password='probably_not_a_secret'):
    IP=edge.get('Internet IP')
    post_fields=json.dumps(config)
    API_CMD = '/api/v1/configs'
    return queryEdge(IP, password, API_CMD, post_fields)


def updateOtherEdgesForGRENode(node):

    edges = buildEdges()

    for edge in edges:
        if node.get("Assigned Edge Name") == edge.get("Name"):
            print("not going to update the edge of this node: " + edge.get("Name"))
        else:
            print("updating " + edge.get("Name"))
    return True


def updateBGPConfig(new_config, edge, assigned_nodes):

    BGP_DEFAULT_AS = 65001
    BGP_PEER_AS = 65002

    new_config["config"]["bgp"] = {
            "neighbors": []
            }

    new_config["config"]["bgp"]["global"] = {
            "as": BGP_DEFAULT_AS,
            "router_id": edge.get("Internet IP"),
            }

    for node in assigned_nodes:
        new_config["config"]["bgp"]["neighbors"].append(
                {
                "enabled": True,
                "neighbor_address": node.get("Local GRE IP"),
                "peer_as": BGP_PEER_AS
                })
    return new_config

def updateFirewallConfig(new_config, edge):

    new_config["config"]["firewall"] = {
            "mode": "PREPEND",
            "tables": [
                {
                    "family": "INET",
                    "name": "appliance",
                    "chains": [
                        {
                            "name": "default_rules",
                            "rules": [
                                {
                                    "comment": "allow gre* to forward",
                                    "rule": "iifname gre* accept",
                                    "sequence_id": 1
                                }
                            ]
                        }
                     ]
                 }
            ]
            }
    return new_config

def updateGREConfig(new_config, edge, assigned_nodes):
    new_config["config"]["interfaces"]["gres"] = []
    for node in assigned_nodes:
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
                "sequence_id": 0,
                "to": node.get("Service IP") + "/32",
                "via": node.get("Remote GRE IP")
            }
            ],
        "source": node.get("Remote Tunnel IP")
        })
    return new_config

def updateStaticAnnouncementsConfig(new_config, edge, assigned_nodes, edges):

    new_config["config"]["scion_tunneling"] = {
            "static_announcements": [],
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

        prefixes = []
        for node in getAssignedNodes(edge_itr):
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
        remotes.append({
            "isd_as": edge_itr["ISD-AS"]
        })
    return new_config

def updateEdgeConfig(edge, edges):
    print("checking edge: " + edge["Name"] + " (" + edge["Internet IP"] + ")...", end="")

    running_config = getEdgeConfig(edge)
    new_config = copy.deepcopy(running_config)

    assigned_nodes = getAssignedNodes(edge)

    updateBGPConfig(new_config, edge, assigned_nodes)

    updateFirewallConfig(new_config, edge)

    updateGREConfig(new_config, edge, assigned_nodes)

    updateStaticAnnouncementsConfig(new_config, edge, assigned_nodes, edges)

    if running_config == new_config:
        print("Configs are still the same - no change to Edge pushed")
    else:
        print("Configs are different - pushing up to Edge")
        putEdgeConfig(edge,new_config)

    return

def updateAllEdgeConfigs():

    print("Reading list of Edges from Notion...", end="")
    edges = getAllAutoConfigEdges()
    print("done. ")
    print("There are " + str(len(edges)) + " Edges set to AutoConfig in Notion.")
    print("")

    for edge in edges:
        updateEdgeConfig(edge, edges)

    return


updateAllEdgeConfigs()

