import json
import pycurl
from io import BytesIO
from io import StringIO

NOTION_API_KEY='YOUR_KEY_HERE'

def buildGRENodes():

  nodes = []

  buffer = BytesIO()
  c = pycurl.Curl()
  c.setopt(c.URL, 'https://api.notion.com/v1/data_sources/28266302-4cb3-8014-a174-000b4ad84140/query')
  c.setopt(c.HTTPHEADER, ['Authorization: Bearer ' + NOTION_API_KEY,
                          'Notion-Version: 2025-09-03',
                          'Content-Type: application/json'])
  c.setopt(c.POST, 1)
  c.setopt(c.POSTFIELDS, '')
  c.setopt(c.WRITEDATA, buffer)
  c.setopt(c.TIMEOUT_MS, 5000)
  c.perform()
  c.close()

  for result in json.loads(buffer.getvalue())['results']:
      nodes.append(buildNodeFromNotionJSON(result))

  return nodes

def buildEdges():

  edges = []

  buffer = BytesIO()
  c = pycurl.Curl()
  c.setopt(c.URL, 'https://api.notion.com/v1/data_sources/27f66302-4cb3-80fb-bec3-000bc8d31c19/query')
  c.setopt(c.HTTPHEADER, ['Authorization: Bearer ' + NOTION_API_KEY,
                          'Notion-Version: 2025-09-03',
                          'Content-Type: application/json'])
  c.setopt(c.POST, 1)
  c.setopt(c.POSTFIELDS, '')
  c.setopt(c.WRITEDATA, buffer)
  c.setopt(c.TIMEOUT_MS, 5000)
  c.perform()
  c.close()

  for result in json.loads(buffer.getvalue())['results'] :
    edges.append(buildEdgeFromNotionJSON(result))

  return edges
      


def areEdgesHealthOK(edges, password='probably_not_a_secret'):
  for edge in edges:
    status = isEdgeHealthOK(edge, password)
    if (False == status):
        return False
  return True


def doLondonPathsExist(edge, password='probably_not_a_secret'):

  post_fields = json.dumps({
  'run': {
    'destination_isd_as': '65-2:0:6c'
   }})


  buffer = BytesIO()
  c = pycurl.Curl()
  c.setopt(c.URL, 'https://' + edge.get('IP') + '/api/v1/tools/scion/showpaths')
  c.setopt(c.SSL_VERIFYPEER, 0)
  c.setopt(c.SSL_VERIFYHOST, 0)
  c.setopt(c.VERBOSE, 0)
  c.setopt(c.TIMEOUT_MS, 5000)
  c.setopt(c.USERNAME, 'admin')
  c.setopt(c.HTTPHEADER, ['Content-Type: application/json'])
  c.setopt(c.PASSWORD, password)
  c.setopt(c.POSTFIELDS, post_fields)
  c.setopt(c.WRITEDATA, buffer)
  c.perform()
  c.close()

  if (len(json.loads(buffer.getvalue())['paths']) > 0):
      return True
  return False

def isEdgeHealthOK(edge, password='probably_not_a_secret'):
  buffer = BytesIO()
  c = pycurl.Curl()
  c.setopt(c.URL, 'https://' + edge.get('IP') + '/api/v1/health')
  c.setopt(c.SSL_VERIFYPEER, 0)
  c.setopt(c.SSL_VERIFYHOST, 0)
  c.setopt(c.TIMEOUT_MS, 5000)
  c.setopt(c.USERNAME, 'admin')
  c.setopt(c.PASSWORD, password)
  c.setopt(c.WRITEDATA, buffer)
  try:
    c.perform()

    for check in json.loads(buffer.getvalue())["health"]["checks"]:
      if not (check.get("status").lower() in ['passing', 'notice']):
              return False
  except pycurl.error as e:
    error_code, error_message = e.args
    print(f"PycURL error: Code {error_code}, Message: {error_message}")
  finally:
    if 'c' in locals() and c is not None:
        c.close()

  return True

def buildNodeFromNotionJSON(json):
    node = {
            "Name": json['properties']['Name']['title'][0]['text']['content'],
            "Edge Internet IP": json['properties']['Edge Internet IP']['rollup']['array'][0]['rich_text'][0]['plain_text'],
            "Service IP": json['properties']['Service IP']['rich_text'][0]['text']['content'],
            "Assigned Edge Name": json['properties']['Assigned Edge Name']['rollup']['array'][0]['title'][0]['plain_text']
    }
    return node

def buildEdgeFromNotionJSON(json):
    edge = {
            "Name": json['properties']['Name']['title'][0]['text']['content'],
            "IP": json['properties']['Internet IP']['rich_text'][0]['text']['content'],
            "Internet IP": json['properties']['Internet IP']['rich_text'][0]['text']['content']
    }
    return edge



def findEdgeByName(name):

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

  buffer = BytesIO()
  c = pycurl.Curl()
  c.setopt(c.URL, 'https://api.notion.com/v1/data_sources/27f66302-4cb3-80fb-bec3-000bc8d31c19/query')
  c.setopt(c.HTTPHEADER, ['Authorization: Bearer ' + NOTION_API_KEY,
                          'Notion-Version: 2025-09-03',
                          'Content-Type: application/json'])
  c.setopt(c.POST, 1)
  c.setopt(c.POSTFIELDS, post_fields )
  c.setopt(c.WRITEDATA, buffer)
  c.setopt(c.TIMEOUT_MS, 5000)
  c.perform()
  c.close()

  for results in json.loads(buffer.getvalue())['results']:
      edges.append(buildEdgeFromNotionJSON(results))

  return edges

def updateEdgeForGRENode(node):
    edge_required_updating = False

    edge = findEdgeByName(node.get("Assigned Edge Name"))[0]

    print("Updating GRE Node + " + node.get("Name") + " at Edge: " + edge.get("Name"))


    config_bgp = "{\"bgp\": {\"global\": {\"as\": 65001}, {\"router_id\": " + edge.get("Internet IP") + "}}}"

    print("    config.bgp: ")
    print(config_bgp)

    print("    add config.bgp.neighbors[N+1] with specific neighbor_address of: " + node.get("Service IP"))
    print("    add config.firewall.table.chains[0] with specific gre* forward")
    print("    add config.interfaces.gre[N+1] with specific dst/src/route")
    print("    add config.scion_tunneling.static_announcements[N+1]")

    return edge_required_updating




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


