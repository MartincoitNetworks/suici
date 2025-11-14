import json
import pycurl
from io import BytesIO


def queryEdge(edge, API_CMD, post_fields=''):

    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, 'https://' + edge['Internet IP'] + API_CMD)
    c.setopt(c.SSL_VERIFYPEER, 0)
    c.setopt(c.SSL_VERIFYHOST, 0)
    c.setopt(c.VERBOSE, 0)
    c.setopt(c.TIMEOUT_MS, 1000)
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
        c.close()
        raise

    response_code = c.getinfo(pycurl.RESPONSE_CODE)
    if response_code in {200,201}:
        json_response = json.loads(buffer.getvalue())
    else:
        print("Edge returned fail response code: " + str(response_code))
        json_response = {}
        json_error_message = json.loads(buffer.getvalue())
        print(json_error_message)

    return json_response
