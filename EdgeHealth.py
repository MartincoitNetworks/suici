import os
import json
import pycurl
from datetime import datetime
import socket

import NotionTools as nt
import EdgeTools as et

EDGE_HEALTH_EXAMS_NOTION_DATABASE='2ab663024cb38022bdb5e3744b31591a'
EDGE_HEALTH_EXAMS_NOTION_DATA_SOURCE='2ab66302-4cb3-807f-870e-000bdb2287e9'

def areEdgesHealthOK(edges):
    all_ok = True
    for edge in edges:
        if (not isEdgeHealthOK(edge)):
            all_ok = False
    return all_ok

def isEdgeHealthOK(edge):

    print("Checking: " + edge.get('Name'))

    API_CMD = '/api/v1/health'
    post_fields = ''

    ok = True

    try:
        response = et.queryEdge(edge, API_CMD, post_fields)
    except Exception as e:
        print(f"No response from {edge.get('Name')}")
        ok = False
    else:
        if not response:
            print(f"Invalid response from {edge.get('Name')}")
            ok = False
        else:
            deleteOldEdgeHealthExam(edge)
            for check in response['health']['checks']:
                if not (check.get("status").lower() in ['passing', 'notice']):
                    print(f"Check failed {edge.get('Name')} {check.get('name')}")
                    addEdgeHealthExam(edge,check)
                    ok = False

    return ok

def getEdgeHealthExams(edge):
    filter_payload = json.dumps({
            "filter": {
                "property": "Edge",
                "relation": { "contains": edge.get('id') }
                }
            })
    return nt.queryNotion(EDGE_HEALTH_EXAMS_NOTION_DATA_SOURCE,filter_payload)


def deleteOldEdgeHealthExam(edge):
    exams = getEdgeHealthExams(edge)
    for exam in exams:
        nt.deletePage(exam.get('id'))
    return

def addEdgeHealthExam(edge,check):

    check_name = check.get('name')
    check_data = json.dumps(check.get('data'))

    current_datetime = datetime.now()
    now_string = current_datetime.strftime('%Y-%m-%dT%H:%M:%SZ')

    examiner = socket.gethostname()

    data = {
          'Name' : {
              'title': [
                  {
                  'text': {
                      'content': edge['Name'] + ' @ ' + now_string + " " + examiner
                      }
                  }
                  ]
              },
           'Edge' : {
              'relation': [
                {
                    'id': edge['id'],
                },
                ]
              },
            'Check': {
                'rich_text': [
                  {
                  'text': {
                    'content': check_name
                    }
                  }
                ]
              },
            'Data': {
                'rich_text': [
                  {
                  'text': {
                    'content': check_data
                    }
                  }
                ]
              }
            }

    payload = json.dumps({"parent": {"database_id": EDGE_HEALTH_EXAMS_NOTION_DATABASE}, "properties": data})

    out = nt.postNotion(payload)
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
