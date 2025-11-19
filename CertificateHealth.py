import os
import json
import copy
import pycurl
from io import BytesIO
from io import StringIO
from cryptography.fernet import Fernet
from jsondiff import diff, symbols
from datetime import datetime
import socket

import NotionTools as nt
import EdgeTools as et

def isEdgeCertificateOK(edge):

    certificate_status = "Unknown"

    print("Checking certificate on: " + edge.get('Name'))

    API_CMD = '/api/v1/health'
    post_fields = ''
    try:
        response = et.queryEdge(edge, API_CMD, post_fields)
    except Exception as e:
        certificate_status = "Unreachable"
        print("No response from: " + edge.get('Name'))
    else:
        for check in response['health']['checks']:
            if check.get("name") == 'Certificate for local AS available':
                if check.get("status").lower() == 'passing':
                    certificate_expiration=check.get("data").get("valid_until")
                    certificate_status = "Passing"
                else:
                    certificate_expiration=check.get("data").get("valid_until")
                    certificate_status = "Failed"
                addCertificateExam(edge,certificate_status,certificate_expiration)

    return certificate_status

def addCertificateExam(edge,certificate_status,certificate_expiration):

  current_datetime = datetime.now()
  now_string = current_datetime.strftime("%Y-%m-%d")

  examiner = socket.gethostname()

  expiration_datetime = datetime.strptime(certificate_expiration,'%Y-%m-%dT%H:%M:%SZ')
  difference = expiration_datetime - current_datetime
  hours_remaining = difference.total_seconds() / 3600

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
            'Certificate Expiration': {
                'date': {
                    'start': certificate_expiration
                },
              },
            'Hours Remaining': {
                'number': hours_remaining
              },
            'Status': {
                'select': {
                    'name': certificate_status
                }
              }
            }

  CERTIFICATE_EXAM_NOTION_DATABASE='2aa663024cb380cd9b26dd3a256631e8'
  payload = json.dumps({"parent": {"database_id": CERTIFICATE_EXAM_NOTION_DATABASE}, "properties": data})

  out = nt.postNotion(payload)
  return


def checkAllEdgeCertificates():

    print("Reading list of Edges from Notion...")
    edges = nt.getAllAutoConfigEdges()
    print("done. ")
    print("There are " + str(len(edges)) + " Edges set to AutoConfig in Notion.")
    print("")

    for edge in edges:
        certificate_is_ok = isEdgeCertificateOK(edge)
        print(f"{edge.get('Name')} certificate is {certificate_is_ok}")

    return

checkAllEdgeCertificates()
