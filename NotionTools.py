#
# 
# sudo pip3 install pycurl
# sudo apt install python3-pycurl
#

import os
import json
import copy
import pycurl
from io import BytesIO
from io import StringIO
from cryptography.fernet import Fernet
from jsondiff import diff, symbols
import time

NODE_NOTION_DATA_SOURCE_ID='28266302-4cb3-8014-a174-000b4ad84140'
EDGE_NOTION_DATA_SOURCE_ID='27f66302-4cb3-80fb-bec3-000bc8d31c19'

def getAPIPasswordEncodingKey():
    try:
        API_PASSWORD_ENCODING_KEY=os.environ['API_PASSWORD_ENCODING_KEY']
    except KeyError as e:
        print(f"")
        print(f"KeyError: {e} - API_PASSWORD_ENCODING_KEY environment variable is not set.")
        print(f"")
        raise

    return API_PASSWORD_ENCODING_KEY

def getNotionAPIKey():

    time.sleep(0.3)
    try:
        NOTION_API_KEY=os.environ['NOTION_API_KEY']
    except KeyError as e:
        print(f"")
        print(f"KeyError: {e} - NOTION_API_KEY environment variable is not set.")
        print(f"")
        raise

    return NOTION_API_KEY

def getAllNodes():
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
  },
  "sorts": [
    {
          "property": "ISD-AS",
	      "direction": "ascending"
	}
	],
  })

  results = queryNotion(EDGE_NOTION_DATA_SOURCE_ID, post_fields)

  for result in results:
    edges.append(getEdgeFromNotionJSON(result))

  return edges

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
            "Edge Operator": response['properties']['Edge Operator']['rollup']['array'][0]['select']['name'],
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
            "ISD-AS": response['properties']['ISD-AS']['rich_text'][0]['text']['content'],
            "API Username": 'admin',
            "API Password": decryptAPIPassword(response['properties']['API Password']['rich_text'][0]['text']['content'])
    }
    return edge

def decryptAPIPassword(encrypted_api_password):
    f = Fernet(getAPIPasswordEncodingKey())
    decrypted_api_password=(f.decrypt(str(encrypted_api_password)).decode("utf-8"))
    return decrypted_api_password

def deletePage(page_id):

    NOTION_API_KEY = getNotionAPIKey()
    post_fields = filter_payload = json.dumps({
            "in_trash": True
            })
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, 'https://api.notion.com/v1/pages/' + page_id)
    c.setopt(c.HTTPHEADER, ['Authorization: Bearer ' + NOTION_API_KEY,
                            'Notion-Version: 2025-09-03',
                            'Content-Type: application/json'])
    c.setopt(c.CUSTOMREQUEST, 'PATCH')
    c.setopt(c.POSTFIELDS, post_fields )
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.TIMEOUT_MS, 5000)
    
    try:
        c.perform()
    except Exception as e:
        time.sleep(1)
        c.perform()

    c.close()
  
    return buffer.getvalue()

def postNotion(post_fields=''):

    NOTION_API_KEY = getNotionAPIKey()

    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, 'https://api.notion.com/v1/pages/')
    c.setopt(c.HTTPHEADER, ['Authorization: Bearer ' + NOTION_API_KEY,
                            'Notion-Version: 2025-09-03',
                            'Content-Type: application/json'])
    c.setopt(c.POST, 1)
    c.setopt(c.POSTFIELDS, post_fields )
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.TIMEOUT_MS, 5000)
    
    try:
        c.perform()
    except Exception as e:
        time.sleep(1)
        c.perform()
    c.close()
  
    return buffer.getvalue()

def queryNotion(data_source_id, post_fields=''):

    NOTION_API_KEY = getNotionAPIKey()

    buffer = BytesIO()
    c = pycurl.Curl()
    url = 'https://api.notion.com/v1/data_sources/' + data_source_id + '/query'
    c.setopt(c.URL, 'https://api.notion.com/v1/data_sources/' + data_source_id + '/query')
    c.setopt(c.HTTPHEADER, ['Authorization: Bearer ' + NOTION_API_KEY,
                            'Notion-Version: 2025-09-03',
                            'Content-Type: application/json'])
    c.setopt(c.POST, 1)
    c.setopt(c.POSTFIELDS, post_fields )
    c.setopt(c.WRITEDATA, buffer)
    c.setopt(c.TIMEOUT_MS, 5000)

    try:
        c.perform()
    except Exception as e:
        time.sleep(1)
        c.perform()
    c.close()

    response = json.loads(buffer.getvalue())
    result = {}
    if "results" in response:
        result = response['results']
    else:
        print(response)
    
    return result


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

    results = queryNotion(EDGE_NOTION_DATA_SOURCE_ID, post_fields)

    for result in results:
        edges.append(getEdgeFromNotionJSON(result))

    return edges
