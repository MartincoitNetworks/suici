import NotionTools as nt
from pyroute2 import IPRoute
from socket import AF_INET
import json
import socket
from datetime import datetime


EXAM_NOTION_DATA_SOURCE_ID='2a5663024cb380579908e83669562666'

BGP_PROTO=186

def printAllEdges():

    print("Reading list of Edges from Notion...", end="")
    edges = nt.getAllAutoConfigEdges()

    for edge in edges:
        print(edge)

    return

def printAllNodeConnectivityStatus():

    SCION_destinations = set()

    ipr = IPRoute()
    for route in ipr.get_routes(family=AF_INET,proto=BGP_PROTO):
        SCION_destinations.add(route.get_attr('RTA_DST'))
    ipr.close()

    examiner_name = socket.gethostname()

    for edge in nt.getAllAutoConfigEdges():
        print(edge['Name'])
        for node in nt.getAssignedNodes(edge):
          print('  ' + node['Name'] + ' ' + node['Service IP'])
          scion_enabled = False
          if node['Service IP'] in SCION_destinations:
            scion_enabled = True

          print(addNotionExam(examiner_name, node, scion_enabled))

    return

def addNotionExam(examiner,node,scion_enabled):

  current_datetime = datetime.now()
  now_string = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

  data = {
          'Name' : {
              'title': [
                  {
                  'text': {
                      'content': examiner + ' examining ' + node['Name'] + ' @ ' + now_string
                      }
                  }
                  ]
              },
          'Examiner' : {
              'rich_text': [
                  {
                  'text': {
                      'content': examiner
                      }
                  }
                  ]
              },
          'Node' : {
              'relation': [
                {
                    'id': node['id'],
                },
                ]
              },
          'SCION Enabled' : {
              'checkbox': scion_enabled
              }
          }
  print(data)

  payload = json.dumps({"parent": {"database_id": EXAM_NOTION_DATA_SOURCE_ID}, "properties": data})

  return nt.postNotion(EXAM_NOTION_DATA_SOURCE_ID, payload)


def CountAllNodesAllEdges():
    return 0

if __name__ == "__main__":
    print("Welcome")
    printAllNodeConnectivityStatus()


