from requests import Session
from requests.auth import HTTPBasicAuth  # or HTTPDigestAuth, or OAuth1, etc.
from zeep import Client
from zeep.transports import Transport

import pandas as pd

session = Session()
session.auth = HTTPBasicAuth('WSuser', '12345')
client = Client('https://c1ex.atollholding.com.ua/C82_P67_AUTOCENTRKIEV/ws/BigData.1cws?wsdl',
    transport=Transport(session=session))

result = client.service.GetDocumentsList(
    documentType='ЗаявкаТО',
    startDate='2023-03-01',
    endDate='2023-06-12',
    docNumber='',
    phone='',
    VIN=''
)

print(pd.DataFrame(result))