import os
import json
import copy
import pycurl
from io import BytesIO
from io import StringIO

def getNotionAPIKey():

    try:
        NOTION_API_KEY=os.environ['NOTION_API_KEY']
    except KeyError as e:
        print(f"")
        print(f"KeyError: {e} - NOTION_API_KEY environment variable is not set.")
        print(f"")
        raise

    return NOTION_API_KEY


def buildGRENodes():

  NOTION_API_KEY = getNotionAPIKey()

  nodes = []

  node_data_source_id='28266302-4cb3-8014-a174-000b4ad84140'
  results = queryNotion(node_data_source_id)

  for result in results:
      nodes.append(buildNodeFromNotionJSON(result))

  return nodes

def buildEdges():

  NOTION_API_KEY = getNotionAPIKey()

  edges = []

  edge_data_source_id = '27f66302-4cb3-80fb-bec3-000bc8d31c19'
  results = queryNotion(edge_data_source_id)

  for result in results:
    edges.append(buildEdgeFromNotionJSON(result))

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

  response = queryEdge(edge.get('IP'), password, API_CMD, post_fields)

  if (len(response['paths']) > 0):
      return True
  return False


  print(results)

#  if (result['paths') > 0):
#      return True
  return False

def isEdgeHealthOK(edge, password='probably_not_a_secret'):

  API_CMD = '/api/v1/health'
  post_fields = ''
  response = queryEdge(edge.get('IP'), password, API_CMD, post_fields)
    
  for check in response['health']['checks']:
      if not (check.get("status").lower() in ['passing', 'notice']):
          return False
  return True

def buildNodeFromNotionJSON(json):

    node = {
            "Name": json['properties']['Name']['title'][0]['text']['content'],
            "Edge GRE ID": str(json['properties']['Edge GRE ID']['number']),
            "Edge Internet IP": json['properties']['Edge Internet IP']['rollup']['array'][0]['rich_text'][0]['plain_text'],
            "Local Tunnel IP": json['properties']['Local Tunnel IP']['rich_text'][0]['text']['content'],
            "Remote Tunnel IP": json['properties']['Remote Tunnel IP']['formula']['string'],
            "Service IP": json['properties']['Service IP']['rich_text'][0]['text']['content'],
            "Assigned Edge Name": json['properties']['Assigned Edge Name']['rollup']['array'][0]['title'][0]['plain_text'],
            'Local GRE IP': json['properties']['Local GRE IP']['formula']['string'],
            'Remote GRE IP': json['properties']['Remote GRE IP']['formula']['string']
    }
    return node

def buildEdgeFromNotionJSON(json):
    edge = {
            "Name": json['properties']['Name']['title'][0]['text']['content'],
            "IP": json['properties']['Internet IP']['rich_text'][0]['text']['content'],
            "Internet IP": json['properties']['Internet IP']['rich_text'][0]['text']['content']
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
      edges.append(buildEdgeFromNotionJSON(result))

  return edges

def getEdgeConfig(edge, password='probably_not_a_secret'):
    IP=edge.get('IP')
    post_fields=''
    API_CMD = '/api/v1/configs/latest'
    return queryEdge(IP, password, API_CMD, post_fields)

def putEdgeConfig(edge, config, password='probably_not_a_secret'):
    IP=edge.get('IP')
    post_fields=json.dumps(config)
    API_CMD = '/api/v1/configs'
    return queryEdge(IP, password, API_CMD, post_fields)



def updateEdgeForGRENode(node):
    edge_required_updating = False

    edge = findEdgeByName(node.get("Assigned Edge Name"))[0]

    running_config = getEdgeConfig(edge)
    new_config = copy.deepcopy(running_config)

    new_config["config"]["bgp"]["global"]["router_id"] = edge.get("Internet IP")

    neighbors = new_config["config"]["bgp"]["neighbors"]
    for neighbor in neighbors:
        if neighbor["neighbor_address"] == node.get("Local GRE IP"):
            neighbors.remove(neighbor)

    new_config["config"]["bgp"]["neighbors"]
    neighbors.append(
            {
                "enabled": True,
                "neighbor_address": node.get("Local GRE IP"),
                "peer_as": 65002,
                "timers": {
                    "hold_time": 3,
                    "keepalive_interval": 1,
                    "minimum_advertisement_interval": 1
                }
            })




    inet_appliance_table = None
    GRE_CHAIN_NAME="Allow_GRE_to_Forward"
    tables = new_config["config"]["firewall"]["tables"]
    for table in tables:
        if table["family"] == "INET" and table["name"] == "appliance":
            inet_appliance_table = table
            chains = table["chains"]
            for chain in chains:
                if chain["name"] == GRE_CHAIN_NAME:
                    chains.remove(chain)

    if not inet_appliance_table:
        inet_appliance_table[chains]=table.append(
                {
                    "name": "appliance",
                    "family": "INET"
                }
                )

    inet_appliance_table["chains"].append(
            {
                "name": GRE_CHAIN_NAME,
                "rules": [
                {
                    "comment": "allow gre* to forward",
                    "rule": "iifname \"gre*\" accept",
                    "sequence_id": 1
                }
                ]
            })

    gres = new_config["config"]["interfaces"]["gres"]
    for gre in gres:
        if gre["destination"] == node.get("Local Tunnel IP"):
            gres.remove(gre)

    gres.append({
        "addresses": [
            node.get("Remote GRE IP") + "/31",
        ],
        "destination": node.get("Local Tunnel IP"),
        "name": "gre" + node.get("Edge GRE ID"),
        "routes": [
            {
                "comment": node.get("Name"),
                "metric": 10,
                "sequence_id": 4,
                "via": node.get("GRE Remote IP"),
                "to": node.get("Service IP") + "/32"
            }
        ],
        "source": node.get("Remote Tunnel IP")
        })

    #print(json.dumps(new_config))
    #return


    announcements = new_config["config"]["scion_tunneling"]["static_announcements"]
    for announcement in announcements:
        if announcement["prefixes"][0] == node.get("Service IP") + "/32":
            announcements.remove(announcement)

    announcements.append({
            "description": node.get("Name"),
            "next_hop_tracking": {
                "target": node.get("Local GRE IP")
            },
            "prefixes": [
                node.get("Service IP") + "/32"
            ],
            "sequence_id": 0
        })

    if running_config == new_config:
        print("Configs are still the same - no change to Edge pushed")
    else:
        print("Configs are different - pushing up to Edge")
        putEdgeConfig(edge,new_config)

    return



print("Reading list of Edges from Notion...", end="")
edges = buildEdges()
print("done. ")
print("There are " + str(len(edges)) + " Edges listed in Notion.")
print("")

for edge in edges:
    print("Checking " + edge.get('Name') + "...")
    print("  Health OK? " + str(isEdgeHealthOK(edge)))
    print("  London Paths in place? " + str(doLondonPathsExist(edge)))

nodes = buildGRENodes()
print("There are " + str(len(nodes)) + " GRE Nodes listed in Notion.")
print("")
for node in nodes:
    print("Checking " + node.get('Name') + "...")
    updateEdgeForGRENode(node)
    print("  The following Remote Edge will need to be updated: ")
    print("    update config.scion_tunneling.domains[N+1]")
    print("    update config.scion_tunneling.remotes")


