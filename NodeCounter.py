#!/usr/bin/env python3

import NotionTools as nt
from pyroute2 import IPRoute
from socket import AF_INET
import json
import socket
from datetime import datetime

EXAM_NOTION_DATABASE='2a5663024cb380579908e83669562666'
EXAM_NOTION_DATASOURCE='2a566302-4cb3-8080-a8bb-000b2bf82554'

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
          scion_enabled = False
          if node['Service IP'] in SCION_destinations:
            scion_enabled = True
          print('  ' + node['Name'] + ' ' + node['Service IP'] + ' SCION:' + str(scion_enabled))

          addNotionExam(examiner_name, node, scion_enabled)

    return

def findTodayNotionExams():
    current_datetime = datetime.now()
    today_string = current_datetime.strftime("%Y-%m-%d")

    filter_payload = json.dumps({
            "filter": {
                "property": "Created time",
                "date": {
                    "on_or_after": today_string
                    }
                }
            })

    return nt.queryNotion(EXAM_NOTION_DATASOURCE, filter_payload)

def addNotionExam(examiner,node,scion_enabled):

  current_datetime = datetime.now()
  now_string = current_datetime.strftime("%Y-%m-%d")

  data = {
          'Name' : {
              'title': [
                  {
                  'text': {
                      'content': node['Name'] + ' @ ' + now_string
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
  payload = json.dumps({"parent": {"database_id": EXAM_NOTION_DATABASE}, "properties": data})

  out = nt.postNotion(payload)
  return out


def CountAllNodesAllEdges():
    return 0

if __name__ == "__main__":
    print("Welcome")
    exams = findTodayNotionExams()
    print(len(exams))

    printAllNodeConnectivityStatus()


