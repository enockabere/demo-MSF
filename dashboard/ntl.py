import requests
from requests import Session
from requests.auth import HTTPBasicAuth
from requests_ntlm import HttpNtlmAuth
import json
import random
import xml.dom.minidom
import xml.etree.ElementTree as ET
from zeep import Client
from zeep.transports import Transport

# session = Session()
# session.auth = HttpNtlmAuth('domain\\fke-admin', 'Administrator#2021!')
# client = Client(
#     'http://102.37.117.22:1447/ADMINBC/WS/FKETEST/Codeunit/MemberPortal', transport=Transport(session=session))


# result = client.service.CreateAccount('Enock', 'enock@gmail.com', '07412229383',
#                                       '2345thtg', 'Nairobi', 'Kenya', '01', 'DIRECT', 'hshshsjshsjjh', '152627bjb')

# print(result)
# session = Session()
# session.auth = HttpNtlmAuth('domain\\fke-admin', 'Administrator#2021!')
# client = Client(
#     'http://102.37.117.22:1447/ADMINBC/WS/FKETEST/Codeunit/MemberPortal', transport=Transport(session=session))


# result = client.service.RegisterEvent('01-003', 'ev00030', 'null',
#                                       )
# print(result)

session = requests.Session()
session.auth = HttpNtlmAuth('domain\\fke-admin', 'Administrator#2021!')
response = session.get(
    "http://102.37.117.22:1448/ADMINBC/ODataV4/Company('FKETEST')/UpcomingEvents")

print(response)
# for access_point in access_points:
#     name = access_point.getAttribute('FnAddContacts')
#     print(name)
