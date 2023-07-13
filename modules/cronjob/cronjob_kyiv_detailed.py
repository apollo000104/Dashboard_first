from requests import Session
from requests.auth import HTTPBasicAuth  # or HTTPDigestAuth, or OAuth1, etc.
from zeep import Client
from zeep.transports import Transport
from zeep import helpers

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Any, Optional
from tqdm import tqdm

import requests

from abc import ABC

import yaml
import json
import sys
import typer
import collections
from pathlib import Path

import warnings
warnings.filterwarnings('ignore')

sys.path.append( str( Path( __file__ ).absolute().parents[ 2 ] ) )

from modules.db import psql

session = Session()
session.auth = HTTPBasicAuth( 'WSuser', '12345' )
client = Client(
    'https://c1ex.atollholding.com.ua/C82_P67_AUTOCENTRKIEV/ws/BigData.1cws?wsdl',
    transport=Transport( session=session )
    )


def _phones( start_date, end_date ):
    try:
        url = f"https://c1ex.atollholding.com.ua/C82_P67_AUTOCENTRKIEV/hs/ws/phones?d1={ str(start_date).replace( '-', '' ) }&d2={ str(end_date).replace( '-', '' ) }"
        response = requests.get(url, auth=('KPIPowerB', 'Dr9xTYJg1R'))
        phones = pd.DataFrame(response.json())
        phones['reportDate'] = pd.to_datetime(phones['reportDate'], format='%Y-%m-%d %H:%M:%S')
        phones['callDate'] = pd.to_datetime(phones['callDate'], format='%d.%m.%Y %H:%M:%S')
        phones_main = phones.drop(['date1', 'date2'], axis=1)
        phones_main = phones_main[[
                'Enterprise', 'EnterpriseCode', 'user', 'reportDate', 'callDate',
                'client', 'phone', 'employee', 'status', 'phoneRecived', 'phoneManager',
                'note', 'phoneEnterprise', 'department', 'group', 'advertisingSource',
                'record', 'callType', 'callTime', 'tellTime'
            ]]
    except Exception as e:
        print(e)
        phones_main = pd.DataFrame(
            columns=[
                'Enterprise', 'EnterpriseCode', 'user', 'reportDate', 'callDate',
                'client', 'phone', 'employee', 'status', 'phoneRecived', 'phoneManager',
                'note', 'phoneEnterprise', 'department', 'group', 'advertisingSource',
                'record', 'callType', 'callTime', 'tellTime'
            ]
        )

    return phones_main

def _get_phones( freq, start_date, end_date ):
    phones_main = pd.DataFrame(
        columns = [
            "Enterprise", "EnterpriseCode", "user", "reportDate", "callDate", "client", "phone",
            "employee", "status", "phoneRecived", "phoneManager", "note", "phoneEnterprise", "department", "group",
            "advertisingSource", "record", "callType", "callTime", "tellTime"
        ] 
    )

    date_range = pd.date_range(start=start_date, end=end_date, freq=freq)

    for start, end in tqdm(zip(date_range, date_range[1:])):

        start = start.date()
        end = end.date()

        print(f'Отримуємо дані з {start} по {end}')

        phones = _phones( start, end )

        phones_main =  pd.concat([phones_main, phones])

    phones_main = phones_main.drop_duplicates()
    
    return phones_main


# _get_phones('20230101', '20230105')
# exit()

def _traffic( start_date, end_date ):
    result = client.service.GetTrafficData(
        startDate=start_date,
        endDate=end_date,
    )

    traffic_main = pd.DataFrame(
        columns = [
            "Период", "ГосударственныйНомер", "ДатаНачала", "ДатаОкончания", "Документ", "Клиент", "Авто", "Направление",
            "ИдентификаторЗаезда", "ИдентификаторКамеры", "ИдентификаторЗоны1", "ИдентификаторЗоны2", "ДатаЗакрытия",
            "Количество", "КоличествоФакт", "Примечание"
        ]
    )

    for doc in tqdm(vars(vars(result)['__values__']['return'])['__values__']['ЗаписьТрафика']):
        try:
            _json = helpers.serialize_object(doc, dict)
            traffic = pd.Series(_json)
            traffic['Период'] = pd.to_datetime(traffic['Период'], format='%Y%m%d %H:%M:%S')
            traffic_main = traffic_main.append(traffic, ignore_index=True)
        except Exception as e:
            print(e)
            print('traffic')
            continue

    return traffic_main


def _get_traffic(freq, start_date, end_date):
    traffic_main = pd.DataFrame(
        columns = [
            "Период", "ГосударственныйНомер", "ДатаНачала", "ДатаОкончания", "Документ", "Клиент", "Авто", "Направление",
            "ИдентификаторЗаезда", "ИдентификаторКамеры", "ИдентификаторЗоны1", "ИдентификаторЗоны2", "ДатаЗакрытия",
            "Количество", "КоличествоФакт", "Примечание"
        ]
    )

    date_range = pd.date_range(start=start_date, end=end_date, freq=freq)

    for start, end in tqdm(zip(date_range, date_range[1:])):

        start = start.date()
        end = end.date()

        print(f'Отримуємо дані з {start} по {end}')

        traffic = _traffic( start, end )

        traffic_main = pd.concat([traffic_main, traffic])

    traffic_main = traffic_main.drop_duplicates()
    
    return traffic_main

# _get_traffic('2023-01-01', '2023-01-05')
# exit()

def _calculate(row):
    kvo = 0
    if row:
        if isinstance(row['Работа'], list):
            for i in row['Работа']:
                kvo = kvo + float(i['Кво'])
        else:
            kvo = float(row['Работа']['Кво'])
        return kvo
    return None

def _application_route_start(row):
    if row is not None:
        if isinstance(row['ЭлементМаршрута'], list):
            return row['ЭлементМаршрута'][0]['ДатаНачала']
        elif isinstance(row['ЭлементМаршрута'], dict):
            return row['ЭлементМаршрута']['ДатаНачала']
    return None

def _application_route_end(row):
    if row is not None:
        if isinstance(row['ЭлементМаршрута'], list):
            if row['ЭлементМаршрута'][-1]['ДатаОкончания'] == '0001-01-01T00:00:00':
                return None
            return row['ЭлементМаршрута'][-1]['ДатаОкончания']
        elif isinstance(row['ЭлементМаршрута'], dict):
            if row['ЭлементМаршрута']['ДатаОкончания'] == '0001-01-01T00:00:00':
                return None
            return row['ЭлементМаршрута']['ДатаОкончания']
    return None

def _check_data_entrance(row):
    if str(row['ДатаЗаезда']) == 'nan':
        return None
    elif '0001-01-01' in str(row['ДатаЗаезда']):
        # string = row['ДатаЗаезда'].split('T')
        # open_date = row['ДатаОткрытия'].split('T')[0]
        # final = open_date + 'T' + string[1]
        return None
    else:
        return row['ДатаЗаезда']

def _to( start_date, end_date, doc_number, phone, vin ):

    result = client.service.GetDocumentsList(
        documentType='ЗаявкаТО',
        startDate=start_date,
        endDate=end_date,
        docNumber=doc_number,
        phone=phone,
        VIN=vin
    )

    to_main = pd.DataFrame(
        columns = [
            'ID', 'Заявка ТО', 'Клієнт', 'Держ. номер', 'Авто', 'Дата відкриття', 'Дата закриття', 'Проведення ЗН', 
            'Дата початку робіт', 'Дата закінчення робіт', 'Нормогодини', 'Категорія', 'Менеджер'
        ]
    )

    for doc in tqdm(vars(result)['__values__']['return']['ЗаявкаТО']):
        try:
            _json = helpers.serialize_object(doc, dict)
            to_raw = pd.Series(_json)
            to_raw = to_raw.replace('0001-01-01T00:00:00', np.nan)
            to = to_raw.copy()

            to['ID'] = to['ДокументID']['УИД']
            to['Заявка ТО'] = to['ДокументID']['Номер'] 
            to['Дата відкриття'] = pd.to_datetime(to['ДатаОткрытия'], format='%Y-%m-%d %H:%M:%S')
            to['Дата закриття'] = pd.to_datetime(to['ДатаЗакрытия'], format='%Y-%m-%d %H:%M:%S')
            to['ДатаЗаезда'] = _check_data_entrance(to)
            # to = to.dropna(subset=['ДатаЗаезда'])

            if to['ДатаЗаезда'] is not None:
                to['Проведення ЗН'] = pd.to_datetime(to['ДатаЗаезда'], format='%Y-%m-%d %H:%M:%S')
            else:
                to['Проведення ЗН'] = None

            to['Клієнт'] = to['Клиент']['Наименование']
            to['Менеджер'] = to['Автор']['Наименование']
            to['Держ. номер'] = to['Авто']['ГосНомер']
            to['Авто'] = to['Авто']['Наименование']

            to['Нормогодини'] = _calculate(to['ТаблицаРабот'])
            to['Категорія'] = to['Категория']
            to['Дата початку робіт'] = _application_route_start(to['МаршрутЗаявки'])
            to['Дата закінчення робіт'] = _application_route_end(to['МаршрутЗаявки'])

            to = to[['ID', 'Заявка ТО', 'Клієнт', 'Держ. номер', 'Авто', 'Дата відкриття', 'Дата закриття', 'Проведення ЗН', 'Дата початку робіт', 'Дата закінчення робіт', 'Нормогодини', 'Категорія', 'Менеджер']].copy()
            to_main = to_main.append(to, ignore_index=True)
        except Exception as e:
            print(e)
            print('TO')
            continue

    to_main[['Дата відкриття', 'Дата закриття', 'Проведення ЗН', 'Дата початку робіт', 'Дата закінчення робіт']] = to_main[['Дата відкриття', 'Дата закриття', 'Проведення ЗН', 'Дата початку робіт', 'Дата закінчення робіт']].fillna('0001-01-01 00:00:00')

    return to_main

def _get_to( freq, start_date, end_date, doc_number, phone, vin ):
    to_main = pd.DataFrame(
        columns = [
            'ID', 'Заявка ТО', 'Клієнт', 'Держ. номер', 'Авто', 'Дата відкриття', 'Дата закриття', 'Проведення ЗН', 
            'Дата початку робіт', 'Дата закінчення робіт', 'Нормогодини', 'Категорія', 'Менеджер'
        ]
    )

    date_range = pd.date_range(start=start_date, end=end_date, freq=freq)

    for start, end in tqdm(zip(date_range, date_range[1:])):

        start = start.date()
        end = end.date()

        print(f'Отримуємо дані з {start} по {end}')

        to = _to( start, end, doc_number, phone, vin )

        to_main = pd.concat([to_main, to])

    to_main = to_main.drop_duplicates('ID')

    return to_main

def _cto( start_date, end_date, doc_number, phone, vin ):
    
    result = client.service.GetDocumentsList(
        documentType='ЗаписьНаСТО',
        startDate=start_date,
        endDate=end_date,
        docNumber=doc_number,
        phone=phone,
        VIN=vin
    )

    cto_main = pd.DataFrame(
        columns = [
            'ID', 'Заявка ТО', 'Створення запис на СТО', 'Плановий заїзд', 'Планове закінчення'
        ]
    )

    for doc in tqdm(vars(result)['__values__']['return']['ЗаписьНаСТО']):
        try:
            _json = helpers.serialize_object(doc, dict)
            cto_raw = pd.Series(_json)
            cto_raw = cto_raw.replace('0001-01-01T00:00:00', np.nan)
            cto = cto_raw.copy()

            cto['ID'] = cto['ДокументID']['УИД']
            if cto['ЗаявкаТО']['ДокументID'] is not None:
                cto['Заявка ТО'] = cto['ЗаявкаТО']['ДокументID']['УИД']
            else:
                cto['Заявка ТО'] = None
            cto['Створення запис на СТО'] = pd.to_datetime(cto['ДокументID']['Дата'], format='%Y-%m-%d %H:%M:%S')
            cto['Плановий заїзд'] = pd.to_datetime(cto['ДатаНачала'], format='%Y-%m-%d %H:%M:%S')
            cto['Планове закінчення'] = pd.to_datetime(cto['ДатаОкончания'], format='%Y-%m-%d %H:%M:%S')

            cto = cto[['ID', 'Заявка ТО', 'Створення запис на СТО', 'Плановий заїзд', 'Планове закінчення']].copy()
            cto_main = cto_main.append(cto, ignore_index=True)
        except Exception as e:
            print(e)
            print('CTO')
            continue

    return cto_main

def _get_cto( freq, start_date, end_date, doc_number, phone, vin ):

    cto_main = pd.DataFrame(
        columns = [
            'ID', 'Заявка ТО', 'Створення запис на СТО', 'Плановий заїзд', 'Планове закінчення'
        ]
    )

    date_range = pd.date_range(start=start_date, end=end_date, freq=freq)

    for start, end in tqdm(zip(date_range, date_range[1:])):

        start = start.date()
        end = end.date()

        print(f'Отримуємо дані з {start} по {end}')

        cto = _cto( start, end, doc_number, phone, vin )

        cto_main = pd.concat([cto_main, cto])

    cto_main = cto_main.drop_duplicates('ID')

    return cto_main
        

class CronjobKyiv( ABC ):
    def update(
        self,
        db: psql.PostgreSQLDB,
        start_date: str,
        end_date: str,
        doc_number: str, 
        phone: str,
        vin: str
    ):
        
        start_date = pd.to_datetime( start_date ).date()
        end_date = pd.to_datetime( end_date ).date()

        # to
        to = db.execute( f'SELECT * FROM "TO"' )
        to = pd.DataFrame( to )

        update = True

        if len( to ) == 0:
            print( f'No data found in "TO"' )
            to1 = _get_to( 'MS', start_date, end_date, doc_number, phone, vin)
            # перевірити у не робочий час
            start = pd.to_datetime(to1[ 'Дата відкриття' ]).max().date() + pd.Timedelta(1, "d")
            to2 = _get_to( 'D', start, end_date, doc_number, phone, vin )
            to = pd.concat([to1, to2])
        else:
            to[ 'Дата відкриття' ] = pd.to_datetime( to[ 'Дата відкриття' ] )
            # print( f"Last data in TO is {to[ 'Дата відкриття' ].max().date()}" )
            start = to[ 'Дата відкриття' ].max().date() + pd.Timedelta(1, "d")
            
            if start > end_date:
                print('Data is up to date in TO')
                update = False
            else:
                to = _get_to( 'D', start, end_date, doc_number, phone, vin )

        if len( to ) > 0 and update:
            db.insert_dataframe( '"TO"', to )
        # ================================================================

        # cto
        cto = db.execute( f'SELECT * FROM "CTO"' )
        cto = pd.DataFrame( cto )

        update = True

        if len( cto ) == 0:
            print( f'No data found in "CTO"' )
            cto1 = _get_cto( 'MS', start_date, end_date, doc_number, phone, vin )
            # перевірити у не робочий час
            start = pd.to_datetime(cto1[ 'Створення запис на СТО' ]).max().date() + pd.Timedelta(1, "d")
            cto2 = _get_cto( 'D', start, end_date, doc_number, phone, vin )
            cto = pd.concat([cto1, cto2])
        else:
            cto[ 'Створення запис на СТО' ] = pd.to_datetime( cto[ 'Створення запис на СТО' ] )
            # print( f"Last data in CTO is {cto[ 'Плановий заїзд' ].max().date()}" )
            start = cto[ 'Створення запис на СТО' ].max().date() + pd.Timedelta(1, "d")
            
            if start > end_date:
                print('Data is up to date in CTO')
                update = False
            else:
                cto = _get_cto( 'D', start, end_date, doc_number, phone, vin )

        if len( cto ) > 0 and update:
            db.insert_dataframe( '"CTO"', cto )
        # ================================================================

        # phones
        phones = db.execute( f'SELECT * FROM "phones"' )
        phones = pd.DataFrame( phones )

        update = True

        if len( phones ) == 0:
            print( f'No data found in "phones"' )
            phones1 = _get_phones( 'MS', start_date, end_date )
            # перевірити у не робочий час
            start = pd.to_datetime(phones1[ 'callDate' ]).max().date() + pd.Timedelta(1, "d")
            phones2 = _get_phones( 'D', start, end_date )
            phones = pd.concat([phones1, phones2])
        else:
            phones[ 'callDate' ] = pd.to_datetime( phones[ 'callDate' ] )
            # print( f"Last data in phones is {phones[ 'callDate' ].max().date()}" )
            start = phones[ 'callDate' ].max().date() + pd.Timedelta(1, "d")

            if start > end_date:
                print('Data is up to date in phones')
                update = False
            else:            
                phones = _get_phones( 'D', start, end_date )

        if len( phones ) > 0 and update:
            db.insert_dataframe( '"phones"', phones )
        # ================================================================

        # traffic
        traffic = db.execute( f'SELECT * FROM "traffic"' )
        traffic = pd.DataFrame( traffic )

        update = True

        if len( traffic ) == 0:
            print( f'No data found in "traffic"' )
            traffic1 = _get_traffic( 'MS', start_date, end_date )
            # перевірити у не робочий час
            start = pd.to_datetime(traffic1[ 'Период' ]).max().date() + pd.Timedelta(1, "d")
            traffic2 = _get_traffic( 'D', start, end_date )
            traffic = pd.concat([traffic1, traffic2])
        else:
            traffic[ 'Период' ] = pd.to_datetime( traffic[ 'Период' ] )
            # print( f"Last data in traffic is {traffic[ 'Период' ].max().date()}" )
            start = traffic[ 'Период' ].max().date() + pd.Timedelta(1, "d")
            
            if start > end_date:
                print('Data is up to date in traffic')
                update = False
            else:
                traffic = _get_traffic( 'D', start, end_date )

        if len( traffic ) > 0 and update:
            db.insert_dataframe( '"traffic"', traffic )
        # ================================================================

def update(
    db_config_path = '/configs/server.yaml',
    start_date = pd.to_datetime('2023-01-01').date(),
    end_date = datetime.now().date(),
    doc_number = None,
    phone = None,
    vin = None,
):
    with open( db_config_path, 'r' ) as f:
        db_config = yaml.safe_load( f )

    db = psql.PostgreSQLDB(
        host=db_config[ 'host' ],
        port=db_config[ 'port' ],
        type=db_config[ 'type' ],
        db=db_config[ 'db' ],
        credentials=db_config[ 'credentials' ],
    )

    adapter = CronjobKyiv()
    adapter.update(
        db,
        start_date,
        end_date,
        doc_number,
        phone,
        vin
    )

update()