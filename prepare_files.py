import pandas as pd
import xmltodict
import json
import numpy as np
from tqdm import tqdm


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

# t = to_raw['МаршрутЗаявки'].apply(lambda x: x['ЭлементМаршрута'][0]['ДатаНачала'] if isinstance(x['ЭлементМаршрута'], list) else x['ЭлементМаршрута']['ДатаНачала'] if isinstance(x['ЭлементМаршрута'], dict) else None)
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
    if row is not None:
        if str(row['ДатаЗаезда']) == 'nan':
            return None
        elif '0001-01-01' in row['ДатаЗаезда']:
            string = row['ДатаЗаезда'].split('T')
            open_date = row['ДатаОткрытия'].split('T')[0]
            final = open_date + 'T' + string[1]
            return final
        else:
            return row['ДатаЗаезда']


def prepare_traffic(exist, paths: list):
    if exist:
        df = pd.read_csv(exist)
    else:
        df = pd.DataFrame()
    for path in tqdm(paths):
        with open(path, 'r') as f:
            traffic_raw = f.read()
            # to_raw = BeautifulSoup(to_raw, 'xml')
            traffic_raw = xmltodict.parse(traffic_raw)
            traffic_raw = json.dumps(traffic_raw, ensure_ascii=False)
            traffic_raw = json.loads(traffic_raw)
            traffic_raw = traffic_raw['soap:Envelope']['soap:Body']['m:GetTrafficDataResponse']['m:return']['ЗаписьТрафика']
            traffic_raw = pd.DataFrame(traffic_raw)
            traffic_raw = traffic_raw.replace('0001-01-01T00:00:00', np.nan)
            traffic = traffic_raw.copy()

            traffic['Период'] = pd.to_datetime(traffic['Период'], format='%Y%m%d %H:%M:%S')
            traffic = traffic.sort_values('Период')

            df = pd.concat([df, traffic])

    df.to_csv('data/new/traffic_full1.csv')
    
    return df
            # traffic = traffic.rename(columns={'ГосударственныйНомер': 'Держ. номер'})
            # traffic_raw = traffic_raw.replace('T', ' ')


def prepare_to(exist, paths: list):
    if exist:
        df = pd.read_csv(exist)
    else:
        df = pd.DataFrame()
    for path in tqdm(paths):
        with open(path, 'r') as f:
            to_raw = f.read()
            # to_raw = BeautifulSoup(to_raw, 'xml')
            to_raw = xmltodict.parse(to_raw)
            to_raw = json.dumps(to_raw, ensure_ascii=False)
            to_raw = json.loads(to_raw)
            to_raw = to_raw['soap:Envelope']['soap:Body']['m:GetDocumentsListResponse']['m:return']['ЗаявкаТО']
            to_raw = pd.DataFrame(to_raw)
            to_raw = to_raw.replace('0001-01-01T00:00:00', np.nan)
            to = to_raw.copy()

            to['ID'] = to['ДокументID'].str['УИД']
            to['Заявка ТО'] = to['ДокументID'].str['Номер'] 
            to['Дата відкриття'] = pd.to_datetime(to['ДатаОткрытия'], format='%Y-%m-%d %H:%M:%S')
            to['Дата закриття'] = pd.to_datetime(to['ДатаЗакрытия'], format='%Y-%m-%d %H:%M:%S')
            to['ДатаЗаезда'] = to.apply(lambda x: _check_data_entrance(x), axis=1)
            to = to.dropna(subset=['ДатаЗаезда'])
            to['Проведення ЗН'] = pd.to_datetime(to['ДатаЗаезда'], format='%Y-%m-%d %H:%M:%S')

            to['Клієнт'] = to['Клиент'].str['Наименование']
            to['Менеджер'] = to['Автор'].str['Наименование']
            to['Держ. номер'] = to['Авто'].str['ГосНомер']
            to['Авто'] = to['Авто'].str['Наименование']
            to['Нормогодини'] = to['ТаблицаРабот'].apply(lambda row: _calculate(row))
            to['Категорія'] = to['Категория']
            to['Дата початку робіт'] = to['МаршрутЗаявки'].apply(lambda x: _application_route_start(x))
            to['Дата закінчення робіт'] = to['МаршрутЗаявки'].apply(lambda x: _application_route_end(x))

            to = to[['ID', 'Заявка ТО', 'Клієнт', 'Держ. номер', 'Авто', 'Дата відкриття', 'Дата закриття', 'Проведення ЗН', 'Дата початку робіт', 'Дата закінчення робіт', 'Нормогодини', 'Категорія', 'Менеджер']].copy()
            # to = to.set_index('ID')

            df = pd.concat([df, to])

    df.to_csv('data/new/to_full1.csv')

    return df


def prepare_cto(exist, paths: list):
    if exist:
        df = pd.read_csv(exist)
    else:
        df = pd.DataFrame()
    for path in tqdm(paths):
        with open(path, 'r') as f:
            cto_raw = f.read()
            # cto_raw = BeautifulSoup(cto_raw, 'xml')
            cto_raw = xmltodict.parse(cto_raw)
            cto_raw = json.dumps(cto_raw, ensure_ascii=False)
            cto_raw = json.loads(cto_raw)
            cto_raw = cto_raw['soap:Envelope']['soap:Body']['m:GetDocumentsListResponse']['m:return']['ЗаписьНаСТО']
            cto_raw = pd.DataFrame(cto_raw)
            cto_raw = cto_raw.replace('0001-01-01T00:00:00', np.nan)
            cto = cto_raw.copy()

            cto['ID'] = cto['ЗаявкаТО'].str['ДокументID'].str['УИД']
            cto['Створення запис на СТО'] = pd.to_datetime(cto['ДокументID'].str['Дата'], format='%Y-%m-%d %H:%M:%S')
            cto['Плановий заїзд'] = pd.to_datetime(cto['ДатаНачала'], format='%Y-%m-%d %H:%M:%S')
            cto['Планове закінчення'] = pd.to_datetime(cto['ДатаОкончания'], format='%Y-%m-%d %H:%M:%S')

            cto = cto[['ID', 'Створення запис на СТО', 'Плановий заїзд', 'Планове закінчення']].copy()
            # cto = cto.set_index('ID')

            df = pd.concat([df, cto])
    
    df.to_csv('data/new/cto_full1.csv')

    return df


prepare_traffic('/Users/aleksandrlozko/stages-customer-service-dashboard-atollhoding1/data/new/traffic_full1.csv', ['/Users/aleksandrlozko/stages-customer-service-dashboard-atollhoding1/data/update/traffic-25052023-12062023'])
prepare_to(None, ['/Users/aleksandrlozko/stages-customer-service-dashboard-atollhoding1/data/update/заявкато-01012023-01032023', '/Users/aleksandrlozko/stages-customer-service-dashboard-atollhoding1/data/update/заявкато-01032023-12062023'])
prepare_cto(None, ['/Users/aleksandrlozko/stages-customer-service-dashboard-atollhoding1/data/update/записьнасто-01012023-01032023', '/Users/aleksandrlozko/stages-customer-service-dashboard-atollhoding1/data/update/записьнасто-01032023-12062023'])