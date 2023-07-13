import warnings
import pandas as pd

pd.options.mode.chained_assignment = None

import json
import xmltodict
import numpy as np
from functools import lru_cache

import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, Input, Output, State, dash_table

AREAS = {
    'Зона ТО і ремонту': ['Клієнт оплачувана', 'Гарантія оплачувана'],
    'Малярно-кузовна дільниця': ['Кузовний ремонт'],
    'Дільниця додаткового обладнання': ['Вст. дод. обладнання. (Оплачувана)', 'Вст. дод. обладнання. докомплектація (НЕ оплачується.)']
}

APPOINTMENT = {
    'За записом': 'Да ',
    'Без запису': 'Нет '
}

def _calculate(row):
    kvo = 0
    if row:
        row = json.loads(row)
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


@lru_cache(maxsize=None)
def get(value_record, value_section, value_manager, start_date, end_date):
    print(value_record, value_section, value_manager, start_date, end_date)
    phones = pd.read_json('data/new/phones_full1.json')
    traffic = pd.read_csv('data/new/traffic_full1.csv')
    to = pd.read_csv('data/new/to_full1.csv', index_col='ID')
    cto = pd.read_csv('data/new/cto_full1.csv', index_col='ID')

    # with open('data/new/Трафик', 'r') as f:
    #     traffic_raw = f.read()
    #     # to_raw = BeautifulSoup(to_raw, 'xml')
    #     traffic_raw = xmltodict.parse(traffic_raw)
    #     traffic_raw = json.dumps(traffic_raw, ensure_ascii=False)
    #     traffic_raw = json.loads(traffic_raw)
    #     traffic_raw = traffic_raw['soap:Envelope']['soap:Body']['m:GetTrafficDataResponse']['m:return']['ЗаписьТрафика']
    #     traffic_raw = pd.DataFrame(traffic_raw)
    #     traffic_raw = traffic_raw.replace('0001-01-01T00:00:00', np.nan)
    #     traffic = traffic_raw.copy()
    #     # traffic = traffic.rename(columns={'ГосударственныйНомер': 'Держ. номер'})
    #     # traffic_raw = traffic_raw.replace('T', ' ')

    # with open('/Users/aleksandrlozko/stages-customer-service-dashboard-atollhoding/data/new/ЗаявкаТО', 'r') as f:
    #     to_raw = f.read()
    #     # to_raw = BeautifulSoup(to_raw, 'xml')
    #     to_raw = xmltodict.parse(to_raw)
    #     to_raw = json.dumps(to_raw, ensure_ascii=False)
    #     to_raw = json.loads(to_raw)
    #     to_raw = to_raw['soap:Envelope']['soap:Body']['m:GetDocumentsListResponse']['m:return']['ЗаявкаТО']
    #     to_raw = pd.DataFrame(to_raw)
    #     to_raw = to_raw.replace('0001-01-01T00:00:00', np.nan)
    #     to = to_raw.copy()

    # with open('/Users/aleksandrlozko/stages-customer-service-dashboard-atollhoding/data/new/ЗаписНаСТО', 'r') as f:
    #     cto_raw = f.read()
    #     # cto_raw = BeautifulSoup(cto_raw, 'xml')
    #     cto_raw = xmltodict.parse(cto_raw)
    #     cto_raw = json.dumps(cto_raw, ensure_ascii=False)
    #     cto_raw = json.loads(cto_raw)
    #     cto_raw = cto_raw['soap:Envelope']['soap:Body']['m:GetDocumentsListResponse']['m:return']['ЗаписьНаСТО']
    #     cto_raw = pd.DataFrame(cto_raw)
    #     cto_raw = cto_raw.replace('0001-01-01T00:00:00', np.nan)
    #     cto = cto_raw.copy()

    phones['callDate'] = pd.to_datetime(phones['callDate'], format='%d.%m.%Y %H:%M:%S')

       # traffic['Период'] = pd.to_datetime(traffic_raw['Период'], format='%d.%m.%Y %H:%M:%S')
    traffic['Период'] = pd.to_datetime(traffic['Период'], format='%Y%m%d %H:%M:%S')
    traffic = traffic.sort_values('Период')

    # Додати фільтр по категоріям
    # to = to[to['Категорія'].isin(['Вст. дод. обладнання. (Оплачувана)', 'Вст. дод. обладнання. докомплектація (НЕ оплачується.)', \
    #                               'Гарантія оплачувана', 'Клієнт оплачувана', 'Кузовний ремонт']) == True]
    # to = to[(to['Держ. номер'] != '-') & (to['Держ. номер'].notna() == True)]
    # ids = [i.text for i in to_raw.find_all('УИД')]

    # В майбутньому перевіряти статус РОБІТ

    # to['ID'] = to['ДокументID'].str['УИД']
    # to['Заявка ТО'] = to['ДокументID'].str['Номер'] 
    # to['Дата відкриття'] = pd.to_datetime(to['ДатаОткрытия'], format='%Y-%m-%d %H:%M:%S')
    # to['Дата закриття'] = pd.to_datetime(to['ДатаЗакрытия'], format='%Y-%m-%d %H:%M:%S')
    # to['ДатаЗаезда'] = to.apply(lambda x: _check_data_entrance(x), axis=1)
    # to = to.dropna(subset=['ДатаЗаезда'])
    # to['Проведення ЗН'] = pd.to_datetime(to['ДатаЗаезда'], format='%Y-%m-%d %H:%M:%S')

    # to['Клієнт'] = to['Клиент'].str['Наименование']
    # to['Держ. номер'] = to['Авто'].str['ГосНомер']
    # to['Авто'] = to['Авто'].str['Наименование']
    # to['Нормогодини'] = to['ТаблицаРабот'].apply(lambda row: _calculate(row))
    # to['Категорія'] = to['Категория']
    # to['Дата початку робіт'] = to['МаршрутЗаявки'].apply(lambda x: _application_route_start(x))
    # to['Дата закінчення робіт'] = to['МаршрутЗаявки'].apply(lambda x: _application_route_end(x))

    # to = to[['ID', 'Заявка ТО', 'Клієнт', 'Держ. номер', 'Авто', 'Дата відкриття', 'Дата закриття', 'Проведення ЗН', 'Дата початку робіт', 'Дата закінчення робіт', 'Нормогодини', 'Категорія']].copy()
    # to = to.set_index('ID')


    # cto['ID'] = cto['ЗаявкаТО'].str['ДокументID'].str['УИД']
    # cto['Створення запис на СТО'] = pd.to_datetime(cto['ДокументID'].str['Дата'], format='%Y-%m-%d %H:%M:%S')
    # cto['Плановий заїзд'] = pd.to_datetime(cto['ДатаНачала'], format='%Y-%m-%d %H:%M:%S')
    # cto['Планове закінчення'] = pd.to_datetime(cto['ДатаОкончания'], format='%Y-%m-%d %H:%M:%S')

    # cto = cto[['ID', 'Створення запис на СТО', 'Плановий заїзд', 'Планове закінчення']].copy()
    # cto = cto.set_index('ID')

    # try to use left joind when we will have заявка то in запис на СТО
    if value_record == 'За записом':
        joined = to.join(cto, lsuffix='ТО', rsuffix='СТО', on=['ID'], how='inner')
    elif value_record == 'Без запису':
        joined = to.join(cto, lsuffix='ТО', rsuffix='СТО', on=['ID'], how='left')
        joined = joined[joined['Створення запис на СТО'].isna() == True]
    
    joined = joined.reset_index()
    joined = joined.drop_duplicates(subset='ID')

    if value_manager == 'Всі':
        pass
    else:
        joined = joined[joined['Менеджер'] == value_manager]

    # joined = joined[joined['За записом'] == APPOINTMENT[value_record]]
    joined['Дата відкриття'] = pd.to_datetime(joined['Дата відкриття'], format='%Y-%m-%d %H:%M:%S')
    joined['Дата закриття'] = pd.to_datetime(joined['Дата закриття'], format='%Y-%m-%d %H:%M:%S')
    joined['Проведення ЗН'] = pd.to_datetime(joined['Проведення ЗН'], format='%Y-%m-%d %H:%M:%S')
    joined['Дата початку робіт'] = pd.to_datetime(joined['Дата початку робіт'], format='%Y-%m-%d %H:%M:%S')
    joined['Дата закінчення робіт'] = pd.to_datetime(joined['Дата закінчення робіт'], format='%Y-%m-%d %H:%M:%S')
    joined['Плановий заїзд'] = pd.to_datetime(joined['Плановий заїзд'], format='%Y-%m-%d %H:%M:%S')
    joined['Планове закінчення'] = pd.to_datetime(joined['Планове закінчення'], format='%Y-%m-%d %H:%M:%S')
    joined['Створення запис на СТО'] = pd.to_datetime(joined['Створення запис на СТО'], format='%Y-%m-%d %H:%M:%S')
    joined = joined[(joined['Дата відкриття'].dt.date >= pd.to_datetime(start_date, format='%Y-%m-%d')) & (joined['Дата відкриття'].dt.date <= pd.to_datetime(end_date, format='%Y-%m-%d'))]
    joined[['Клієнт', 'Держ. номер', 'Авто']] = joined[['Клієнт', 'Держ. номер', 'Авто']].astype(str).apply(lambda x: x.str.strip())


    main = pd.DataFrame(
        index=joined.index,
        columns=['ПІБ', 'Телефон', 'Держ. номер', 'Марка і модель', 'Вхідний дзвінок', 'Втрачений дзвінок', 'Створення запис на СТО', \
                 'Створення ЗН', 'Плановий заїзд', 'Проведення ЗН', 'Дата початку робіт', 'Заїзд на парковку', 'Заїзд в зону сервісу', \
                 'Виїзд з зони сервісу', 'Дата закінчення робіт', 'Планове закінчення', 'Закриття ЗН', 'Виїзд з території', 
                 'Нормогодини', 'Категорія', 'Менеджер', 'Заявка ТО'])
    
    main['ПІБ'] = joined['Клієнт']
    main['Телефон'] = None
    main['Держ. номер'] = joined['Держ. номер']
    main['Марка і модель'] = joined['Авто']
    main['Вхідний дзвінок'] = None
    main['Втрачений дзвінок'] = None
    main['Створення запис на СТО'] = joined['Створення запис на СТО']
    main['Створення ЗН'] = joined['Дата відкриття']
    main['Плановий заїзд'] = joined['Плановий заїзд']
    main['Проведення ЗН'] = joined['Проведення ЗН']
    main['Дата початку робіт'] = joined['Дата початку робіт']
    main['Заїзд на парковку'] = None
    main['Заїзд в зону сервісу'] = None
    main['Виїзд з зони сервісу'] = None
    main['Дата закінчення робіт'] = joined['Дата закінчення робіт']
    main['Планове закінчення'] = joined['Планове закінчення']
    main['Закриття ЗН'] = joined['Дата закриття']
    main['Виїзд з території'] = None
    main['Нормогодини'] = joined['Нормогодини']
    main['Категорія'] = joined['Категорія']
    main['Менеджер'] = joined['Менеджер']
    main['Заявка ТО'] = joined['Заявка ТО']

    # print(main[main['ПІБ'] == 'Липовенко Ігор Вікторович '])

    for i, row in joined.iterrows():

        # if row['Клієнт'] == 'Малець Андрій Михайлович':
        #     r = (
        #         abs(
        #             pd.to_datetime(main['Виїзд з території'], format='%Y.%m.%d %H:%M:%S') - pd.to_datetime(main['Плановий заїзд'], format='%d.%m.%Y %H:%M:%S')
        #         ) - abs(
        #             pd.to_datetime(main['Створення ЗН'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Створення запис на СТО'], format='%d.%m.%Y %H:%M:%S'))
        #         ).dt.total_seconds() / 60
        #     t = (abs(pd.to_datetime(main['Виїзд з території'], format='%Y.%m.%d %H:%M:%S') - pd.to_datetime(main['Плановий заїзд'], format='%d.%m.%Y %H:%M:%S')))
        #     f = (abs(pd.to_datetime(main['Створення ЗН'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Створення запис на СТО'], format='%d.%m.%Y %H:%M:%S')))
        #     print(r)
        #     print(t)
        #     print(f)


        incoming_client_number = None
        missed_client_number = None
        first_incoming = None
        
        # incoming_call не зовсім incoming
        # може бути ситуація, коли клієнт зателефонував у не робочий час
        # і йому передзвонили та зробили запис на СТО
        # тобто фіксування ймовірного запису
        first_incoming_phones = phones[
                (phones['client'].str.strip() == row['Клієнт'].strip()) & (phones['status'] == 'ANSWERED') & \
                    (phones['callDate'] < row['Створення запис на СТО'] + pd.Timedelta(5, 'm')) & \
                        (phones['callDate'] > row['Створення запис на СТО'] - pd.Timedelta(14, 'd'))
                        ]
        first_incoming_call = pd.to_datetime(first_incoming_phones['callDate'], format='%d.%m.%Y %H:%M:%S')
        call_duration = first_incoming_phones['tellTime']
        first_incoming_index = first_incoming_call.searchsorted(row['Створення запис на СТО'])

        if len(first_incoming_call):
            # if row['Клієнт'] == 'Мартинюк Микола Миколайович':
            #     print(incoming_call)
            #     print(incoming_index)
            #     print(row['Створення запис на СТО'])
            if first_incoming_index == len(first_incoming_call):
                first_incoming_index = first_incoming_index - 1
            main.loc[i, ['Вхідний дзвінок']] = first_incoming_call.iloc[first_incoming_index] - pd.Timedelta(int(call_duration.iloc[first_incoming_index]), 'sec')
            # print('first', first_incoming_call.iloc[first_incoming_index])
            incoming_client_number = first_incoming_phones['phone'].iloc[first_incoming_index]
            first_incoming = True

        # if row['Клієнт'] == 'Сандирєв Данило Леонідович':
        #     print(incoming_call)
        #     print(incoming_index)
                

        # отримуємо перший втрачений дзвінок за три дні до запису
        # можливо треба виправити віднімання 3х днів від зати запису, щоб захватити більше дзвінків 
        # використати np.floor()
        missed_phones = phones[
                (phones['client'].str.strip() == row['Клієнт'].strip()) & (phones['callType'] == 'Вхідний') & ((phones['status'] == 'NO_ANSWER') | \
                        (phones['status'] == 'NOT WORKING TIME')) & (row['Створення запис на СТО'] - pd.Timedelta(3, 'd') < \
                            phones['callDate']) & (phones['callDate'] < row['Створення запис на СТО'])]
        missed_call = pd.to_datetime(missed_phones['callDate'], format='%d.%m.%Y %H:%M:%S')
        if len(missed_call):
            if main['Вхідний дзвінок'].loc[i] and missed_call.iloc[0]:
                if missed_call.iloc[0] < main['Вхідний дзвінок'].loc[i]:
                    main.loc[i, ['Втрачений дзвінок']] = missed_call.iloc[0]
            else:
                main.loc[i, ['Втрачений дзвінок']] = missed_call.iloc[0]
            missed_client_number = missed_phones['phone'].iloc[0]


        # if first_incoming:
        #     incoming_phones = phones[
        #             (phones['client'] == row['Клієнт']) & (phones['status'] == 'ANSWERED') & \
        #                 (phones['callDate'] > first_incoming_call.iloc[first_incoming_index])]
        #     incoming_call = pd.to_datetime(incoming_phones['callDate'], format='%d.%m.%Y %H:%M:%S')
        #     call_duration = incoming_phones['tellTime']
        #     incoming_index = incoming_call.searchsorted(first_incoming_call.iloc[first_incoming_index])

        #     if len(incoming_call):
        #         if incoming_index == len(incoming_call):
        #             incoming_index = incoming_index - 1
        #         main.loc[i, ['Вхідний дзвінок']] = incoming_call.iloc[incoming_index] - pd.Timedelta(int(call_duration.iloc[incoming_index]), 'sec')
        #         print('last', incoming_call.iloc[incoming_index])
        #         print('-------')
        #         incoming_client_number = incoming_phones['phone'].iloc[incoming_index]


        if incoming_client_number and missed_client_number:
            if incoming_client_number == missed_client_number:
                main.loc[i, ['Телефон']] = incoming_client_number
            else:
                main.loc[i, ['Телефон']] = incoming_client_number + '/' + missed_client_number
        elif incoming_client_number:
            main.loc[i, ['Телефон']] = incoming_client_number
        elif missed_client_number:
            main.loc[i, ['Телефон']] = missed_client_number

        # if row['Клієнт'].strip() == "Чайка Андрій Анатолійович":
        #     print(missed_phones)
        #     print(missed_call)
        #     print(main.loc[i, ['Втрачений дзвінок']])
        #     print(main.loc[i, ['Телефон']])
                
        traffic_row = traffic[(traffic['ГосударственныйНомер'] == row['Держ. номер'])]
        if len(traffic_row):
            closest_id = traffic_row['Период'].searchsorted(pd.to_datetime(row['Дата відкриття'], format='%d.%m.%Y %H:%M:%S'))
            if closest_id == len(traffic_row):
                closest_id = closest_id - 1
            id_race = traffic_row.iloc[closest_id]['ИдентификаторЗаезда']
            # if row['Клієнт'] == 'Новіков Віктор Володимирович ':
            #     print(row['Відкрита'])
            #     print(sorted_traffic)
            #     print(closest_id)
            #     print(id_race)
            # print(id_race)
        else: 
            continue

        entering_parking = pd.to_datetime(
            traffic[
                (traffic['ГосударственныйНомер'] == row['Держ. номер']) & ((traffic['ИдентификаторЗоны1'] == 'Main Entrance Terminal') | \
                    (traffic['ИдентификаторЗоны1'] == 'Main Entrance Camera') | (traffic['ИдентификаторЗоны1'] == 'Service exit')) & \
                        (traffic['ИдентификаторЗоны2'] == 'Город') & (traffic['ИдентификаторЗаезда'] == id_race)]['ДатаНачала'],
            format='%Y.%m.%d %H:%M:%S')

        if len(entering_parking):
            if len(entering_parking) > 1:
                entering_parking = entering_parking.iloc[-1]
            else:
                entering_parking = entering_parking.iloc[0]
            main.loc[i, ['Заїзд на парковку']] = entering_parking


        entering_service =pd.to_datetime(
            traffic[
                ((traffic['ГосударственныйНомер'] == row['Держ. номер']) & (traffic['ИдентификаторЗаезда'] == id_race) & \
                    ((traffic['ИдентификаторЗоны1'] == 'Main Entrance Terminal') | (traffic['ИдентификаторЗоны1'] == 'Main Entrance Camera') | \
                    (traffic['ИдентификаторЗоны1'] == 'Service (in/out) Camera 1') | (traffic['ИдентификаторЗоны1'] == 'Service (in/out) Camera 2')) & \
                        ((traffic['ИдентификаторЗоны2'] == 'Service (in/out) Camera 1') | (traffic['ИдентификаторЗоны2'] == 'Service (in/out) Camera 2') | \
                         (traffic['ИдентификаторЗоны2'] == 'Service In Camera')))]['Период'], 
            format='%Y.%m.%d %H:%M:%S')
    

        if len(entering_service):
            # if len(entering_service) > 1:
            #     entering_service = entering_service.iloc[-1]
            # else:
            entering_service = entering_service.iloc[0]
            main.loc[i, ['Заїзд в зону сервісу']] = entering_service


        departure_service = pd.to_datetime(
            traffic[
                (traffic['ГосударственныйНомер'] == row['Держ. номер']) & ((traffic['ИдентификаторЗоны1'] == 'Service exit') | \
                    (traffic['ИдентификаторЗоны1'] == 'Service (in/out) Camera 1') | (traffic['ИдентификаторЗоны1'] == 'Service (in/out) Camera 2')) & \
                        (traffic['ИдентификаторЗаезда'] == id_race)]['ДатаНачала'],
            format='%Y.%m.%d %H:%M:%S')
        
        if len(departure_service):
            # if len(departure_service) > 1:
            #     departure_service_list.append(departure_service.iloc[0])
            # else:
                # departure_service = departure_service.iloc[0]
                main.loc[i, ['Виїзд з зони сервісу']] = departure_service.iloc[-1]


        departure_parking = pd.to_datetime(
            traffic[
                (traffic['ГосударственныйНомер'] == row['Держ. номер']) & ((traffic['ИдентификаторЗоны1'] == 'Main Entrance Terminal') | \
                    (traffic['ИдентификаторЗоны1'] == 'Main Entrance Camera') | (traffic['ИдентификаторЗоны1'] == 'Service (in/out) Camera 1') | \
                        (traffic['ИдентификаторЗоны1'] == 'Service (in/out) Camera 2') | (traffic['ИдентификаторЗоны1'] == 'Service exit')) & \
                        ((traffic['ИдентификаторЗоны2'] == 'Город') | (traffic['ИдентификаторЗоны2'] == 'Main Exit Camera')) & \
                            (traffic['ИдентификаторЗаезда'] == id_race)]['Период'], 
            format='%Y.%m.%d %H:%M:%S')
        if len(departure_parking):
            if len(departure_parking) > 1:
                 main.loc[i, ['Виїзд з території']] = departure_parking.iloc[-1]
            else:
                 main.loc[i, ['Виїзд з території']] = departure_parking.iloc[0]

    main['Вхідний дзвінок'] = pd.to_datetime(main['Вхідний дзвінок'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    main['Втрачений дзвінок'] = pd.to_datetime(main['Втрачений дзвінок'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    main['Створення запис на СТО'] = pd.to_datetime(main['Створення запис на СТО'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    main['Створення ЗН'] = pd.to_datetime(main['Створення ЗН'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    main['Плановий заїзд'] = pd.to_datetime(main['Плановий заїзд'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    main['Заїзд на парковку'] = pd.to_datetime(main['Заїзд на парковку'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    main['Заїзд в зону сервісу'] = pd.to_datetime(main['Заїзд в зону сервісу'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    main['Виїзд з зони сервісу'] = pd.to_datetime(main['Виїзд з зони сервісу'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    # main['Закінчення запису на СТО'] = pd.to_datetime(main['Закінчення запису на СТО'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    main['Закриття ЗН'] = pd.to_datetime(main['Закриття ЗН'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    main['Виїзд з території'] = pd.to_datetime(main['Виїзд з території'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')

    if value_section != 'Всі':
        # main = main[main['Категорія'].isin(AREAS[value_section])].apply(np.ceil)
        main = main[main['Категорія'].isin(AREAS[value_section])]
    else:
        # main = main.apply(np.ceil)
        main = main


    if value_record == 'За записом':
        record_analytics_mean = pd.DataFrame(
            columns = [
                'Контакт з клієнтом', 'Підготовка до візиту', 
                'Прийомка', 'У т. ч. очікування прийому', 'Очікування ремонту', 'Ремонт загальний', 'Ремонт відсканований', 
                'Очікування в ремзоні (простої)', 'Видача', 'Перебування авто після завершення ремонту', 
                'Клієнт очікує призначеної дати візиту, діб', 'Тривалість візиту, години',
                'Шлях клієнта з запису, діб', 'Коефіцієнт ефективності'
            ]
        )

        record_analytics_mean['Клієнт очікує призначеної дати візиту, діб'] = abs(pd.to_datetime(main['Плановий заїзд'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Створення запис на СТО'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 86400
        # record_analytics_mean['Обробка втраченого звінка'] = abs(pd.to_datetime(main['Вхідний дзвінок'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Втрачений дзвінок'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Контакт з клієнтом'] = abs(pd.to_datetime(main['Створення запис на СТО'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Вхідний дзвінок'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        # record_analytics_mean['Шлях клієнта з першого контакту'] = (abs(pd.to_datetime(main['Виїзд з території'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Вхідний дзвінок'], format='%d.%m.%Y %H:%M:%S')) - abs(pd.to_datetime(main['Створення ЗН'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Створення запис на СТО'], format='%d.%m.%Y %H:%M:%S'))).dt.total_seconds() / 60
        record_analytics_mean['Шлях клієнта з запису, діб'] = (abs(pd.to_datetime(main['Виїзд з території'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Плановий заїзд'], format='%d.%m.%Y %H:%M:%S'))).dt.total_seconds() / 86400
        record_analytics_mean['Підготовка до візиту'] = (pd.to_datetime(main['Плановий заїзд'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Створення ЗН'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['У т. ч. очікування прийому'] = (pd.to_datetime(main['Проведення ЗН'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Прийомка'] = (pd.to_datetime(main['Заїзд в зону сервісу'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Очікування ремонту'] = (pd.to_datetime(main['Заїзд в зону сервісу'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Проведення ЗН'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Ремонт загальний'] = abs(pd.to_datetime(main['Виїзд з зони сервісу'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд в зону сервісу'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        # record_analytics_mean['Ремонт відсканований'] = (pd.to_datetime(main['Дата закінчення робіт'], format='%Y.%m.%d %H:%M:%S') - pd.to_datetime(main['Дата початку робіт'], format='%Y.%m.%d %H:%M:%S')).dt.total_seconds / 60
        record_analytics_mean['Ремонт відсканований'] = 0
        # record_analytics_mean['Очікування в ремзоні (простої)'] = record_analytics_mean['Ремонт загальний'] - record_analytics_mean['Ремонт відсканований']
        record_analytics_mean['Очікування в ремзоні (простої)'] = 0
        record_analytics_mean['Видача'] = abs(pd.to_datetime(main['Закриття ЗН'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Виїзд з зони сервісу'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Перебування авто після завершення ремонту'] = (pd.to_datetime(main['Виїзд з території'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Закриття ЗН'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Тривалість візиту, години'] = abs(pd.to_datetime(main['Виїзд з території'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 3600
        # record_analytics_mean['Відхилення від запланованого часу прибуття клієнта'] = abs(pd.to_datetime(main['Плановий заїзд'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Коефіцієнт ефективності'] = (main['Нормогодини'] / (record_analytics_mean['Ремонт загальний'] / 60)).round(2)
        # record_analytics_mean['Коефіцієнт ефективності'] = record_analytics_mean['Коефіцієнт ефективності'].astype('object')
        # record_analytics_mean['Нормогодини'] = main['Нормогодини']
        record_analytics_mean['Менеджер'] = main['Менеджер']

        record_analytics_mean['Категорія'] = main['Категорія']

        if value_section != 'Всі':
            record_mean_areas = record_analytics_mean[record_analytics_mean['Категорія'].isin(AREAS[value_section])].describe().loc[['count', 'mean', 'min', 'max']].apply(np.ceil)
        else:
            record_mean_areas = record_analytics_mean.describe().loc[['count', 'mean', 'min', 'max']].apply(np.ceil)
        record_mean_areas = record_mean_areas.rename(
            index={'count': 'Кількість заїздів по запису', 'mean': 'Середнє', 'min': 'Мінімальне', 'max': 'Максимальне'}
        )
        record_mean_areas = record_mean_areas.reset_index()
        record_mean_areas = record_mean_areas.rename(
            columns={'index': 'Показник'}
        )
        records = record_analytics_mean
        describe_areas = record_mean_areas
        
    elif value_record == 'Без запису':
        without_record_analytics_mean = pd.DataFrame(
            columns = [
                'Очікування клієнта в черзі', 'Прийомка', 'Очікування ремонту', 'Ремонт загальний', 
                'Ремонт відсканований', 'Очікування в ремзоні (простої)', 'Видача', 'Перебування авто після завершення ремонту', 
                'Тривалість візиту, години', 'Коефіцієнт ефективності'
            ]
        )

        without_record_analytics_mean['Очікування клієнта в черзі'] = abs(pd.to_datetime(main['Створення ЗН'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        without_record_analytics_mean['Прийомка'] = (pd.to_datetime(main['Заїзд в зону сервісу'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        without_record_analytics_mean['Очікування ремонту'] = (pd.to_datetime(main['Заїзд в зону сервісу'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Проведення ЗН'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        without_record_analytics_mean['Ремонт загальний'] = abs(pd.to_datetime(main['Виїзд з зони сервісу'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд в зону сервісу'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        # without_record_analytics_mean['Ремонт відсканований'] = (pd.to_datetime(main['Дата закінчення робіт'], format='%Y.%m.%d %H:%M:%S') - pd.to_datetime(main['Дата початку робіт'], format='%Y.%m.%d %H:%M:%S')).dt.total_seconds / 60
        without_record_analytics_mean['Ремонт відсканований'] = 0
        # without_record_analytics_mean['Очікування в ремзоні (простої)'] = without_record_analytics_mean['Ремонт загальний'] - without_record_analytics_mean['Ремонт відсканований']
        without_record_analytics_mean['Очікування в ремзоні (простої)'] = 0
        without_record_analytics_mean['Видача'] = abs(pd.to_datetime(main['Закриття ЗН'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Виїзд з зони сервісу'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        without_record_analytics_mean['Перебування авто після завершення ремонту'] = (pd.to_datetime(main['Виїзд з території'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Закриття ЗН'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        without_record_analytics_mean['Тривалість візиту, години'] = abs(pd.to_datetime(main['Виїзд з території'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 3600
        without_record_analytics_mean['Коефіцієнт ефективності'] = (main['Нормогодини'] / (without_record_analytics_mean['Ремонт загальний'] / 60)).round(2)
        without_record_analytics_mean['Категорія'] = main['Категорія']
        without_record_analytics_mean['Менеджер'] = main['Менеджер']

        # просто для groupby
        without_record_analytics_mean['Підготовка до візиту'] = 0
        without_record_analytics_mean['Клієнт очікує призначеної дати візиту, діб'] = 0
        without_record_analytics_mean['Шлях клієнта з запису, діб'] = 0

        if value_section != 'Всі':
            without_record_mean_areas = without_record_analytics_mean[without_record_analytics_mean['Категорія'].isin(AREAS[value_section])].describe().loc[['count', 'mean', 'min', 'max']].apply(np.ceil)
        else:
            without_record_mean_areas = without_record_analytics_mean.describe().loc[['count', 'mean', 'min', 'max']].apply(np.ceil)
        without_record_mean_areas = without_record_mean_areas.rename(
            index={'count': 'Кількість', 'mean': 'Середнє', 'min': 'Мінімальне', 'max': 'Максимальне'}
        )
        without_record_mean_areas = without_record_mean_areas.reset_index()
        without_record_mean_areas = without_record_mean_areas.rename(
            columns={'index': 'Показник'}
        )
        records = without_record_analytics_mean
        describe_areas = without_record_mean_areas

    if value_record == 'За записом':
        # len_to = len(to)

        table2 = records.groupby('Менеджер').agg(
            # all_all=('Менеджер', lambda x: x.sum() if x in to['Менеджер'].to_list()),
            all_with=('Менеджер', 'count'),
            prepared=('Підготовка до візиту', lambda x: (x.astype(int) >= 15).sum()),
            not_prepared=('Підготовка до візиту', lambda x: (x.astype(int) < 15).sum()),
            closed_after=('Перебування авто після завершення ремонту', lambda x: (x < 0).sum())
        )
        table2 = table2.reset_index()

        to['Дата відкриття'] = pd.to_datetime(to['Дата відкриття'], format='%Y-%m-%d %H:%M:%S')
        all_rec = to[(to['Дата відкриття'].dt.date >= pd.to_datetime(start_date, format='%Y-%m-%d')) & (to['Дата відкриття'].dt.date <= pd.to_datetime(end_date, format='%Y-%m-%d'))].groupby('Менеджер').agg(
            all=('Менеджер', 'count')
        ).reset_index()
        all_rec = all_rec.rename(columns={'all': 'Кількість заїздів всього'})
        not_all_rec = all_rec[~all_rec['Менеджер'].isin(list(table2['Менеджер']))]
        all_rec = all_rec[all_rec['Менеджер'].isin(list(table2['Менеджер']))]
        new_rec = pd.Series([all_rec['Кількість заїздів всього'].sum()] + all_rec['Кількість заїздів всього'].to_list())

        table2 = pd.concat([pd.DataFrame([['Всього'] + [0] * (len(table2.columns) - 1)], columns=table2.columns), table2], ignore_index=True)
        new_column = pd.Series(new_rec, name='Кількість заїздів всього')
        table2 = pd.concat([new_column, table2], axis=1)
        # table2['Кількість заїздів всього'] = new_rec
        
        percent = (table2['prepared'] * 100) / table2['all_with']
        table2.insert(3, '% підготовлених заїздів', percent.round(2))
        table2 = table2.rename(columns={'all_with': 'Кількість заїздів по запису', 'prepared': 'Кількість Н-З, підготовлених завчасно', 'not_prepared': 'Кількість Н-З НЕ підготовлених завчасно', 'percent': '% підготовлених заїздів', 'closed_after': 'Кількість заїздів закритих після виїзду клієнта'})
        table2 = table2.transpose()
        table2 = table2.reset_index()
        table2.columns = table2.iloc[1]
        table2 = table2.drop(1, axis=0)
        table2 = table2.set_index('Менеджер')
        # table2.insert(0, 'Всього', table2.loc[(table2.index != '% підготовлених заїздів') | (table2.index != 'Кількість заїздів всього'), table2.columns].sum(axis=1))
        # table2.insert(0, 'Всього', table2.loc[table2.index != '% підготовлених заїздів', table2.columns].sum(axis=1))
        # table2['Всього'] = table2.loc[(table2.index != '% підготовлених заїздів') | (table2.index != 'Кількість заїздів всього'), table2.columns].sum(axis=1)
        # table2['Всього'] = table2.apply(lambda row: row[table2.columns[table2.columns != 'Всього']].sum() if (row.index != '% підготовлених заїздів') | (row.index != 'Кількість заїздів всього') else None)
        if value_manager == 'Всі':
            for _, row in not_all_rec.iterrows():
                table2[row['Менеджер']] = 0
                table2.loc['Кількість заїздів всього', row['Менеджер']] = row['Кількість заїздів всього']

        table2['Всього'] = table2.loc[:, table2.columns != 'Всього'].sum(axis=1)
        table2.loc['% підготовлених заїздів', 'Всього'] = (table2.loc['Кількість Н-З, підготовлених завчасно', 'Всього'] * 100 / table2.loc['Кількість заїздів по запису', 'Всього']).round(2)
        table2 = table2.reset_index()
        table2 = table2.rename(columns={'index': 'Менеджер'})

        table2 = table2.iloc[:5].append(table2.iloc[2], ignore_index=True).append(table2.iloc[5:], ignore_index=True)
        table2 = table2.drop(2, axis=0)
        # total_arrivals = table2.pop('Кількість заїздів всього')
        # table2.insert(0, 'Кількість заїздів всього', total_arrivals)
        # table2 = pd.concat([table2.iloc['Кількість заїздів всього'], table2.iloc[:'Кількість заїздів всього']])
        # table2.append('Кількість заїздів всього', new_rec)
        records = records.drop('Менеджер', axis=1)
    
    elif value_record == 'Без запису':
        table2 = records.groupby('Менеджер').agg(
            # all_all=('Менеджер', lambda x: x.sum() if x in to['Менеджер'].to_list()),
            all_with=('Менеджер', 'count'),
            prepared=('Підготовка до візиту', lambda x: (x.astype(int) >= 15).sum()),
            not_prepared=('Підготовка до візиту', lambda x: (x.astype(int) < 15).sum()),
            closed_after=('Перебування авто після завершення ремонту', lambda x: (x < 0).sum())
        )
        table2 = table2.reset_index()

        to['Дата відкриття'] = pd.to_datetime(to['Дата відкриття'], format='%Y-%m-%d %H:%M:%S')
        all_rec = to[(to['Дата відкриття'].dt.date >= pd.to_datetime(start_date, format='%Y-%m-%d')) & (to['Дата відкриття'].dt.date <= pd.to_datetime(end_date, format='%Y-%m-%d'))].groupby('Менеджер').agg(
            all=('Менеджер', 'count')
        ).reset_index()
        all_rec = all_rec.rename(columns={'all': 'Кількість заїздів всього'})
        all_rec = all_rec[all_rec['Менеджер'].isin(list(table2['Менеджер']))]
        new_rec = pd.Series([all_rec['Кількість заїздів всього'].sum()] + all_rec['Кількість заїздів всього'].to_list())

        table2 = pd.concat([pd.DataFrame([['Всього'] + [0] * (len(table2.columns) - 1)], columns=table2.columns), table2], ignore_index=True)
        new_column = pd.Series(new_rec, name='Кількість заїздів всього')
        table2 = pd.concat([new_column, table2], axis=1)
        # table2['Кількість заїздів всього'] = new_rec
        
        table2.insert(3, '% підготовлених заїздів', [0] * len(new_rec))
        table2 = table2.rename(columns={'all_with': 'Кількість заїздів по запису', 'prepared': 'Кількість Н-З, підготовлених завчасно', 'not_prepared': 'Кількість Н-З НЕ підготовлених завчасно', 'percent': '% підготовлених заїздів', 'closed_after': 'Кількість заїздів закритих після виїзду клієнта'})
        table2 = table2.transpose()
        table2 = table2.reset_index()
        table2.columns = table2.iloc[1]
        table2 = table2.drop(1, axis=0)
        table2 = table2.set_index('Менеджер')
        # table2.insert(0, 'Всього', table2.loc[(table2.index != '% підготовлених заїздів') | (table2.index != 'Кількість заїздів всього'), table2.columns].sum(axis=1))
        # table2.insert(0, 'Всього', table2.loc[table2.index != '% підготовлених заїздів', table2.columns].sum(axis=1))
        # table2['Всього'] = table2.loc[(table2.index != '% підготовлених заїздів') | (table2.index != 'Кількість заїздів всього'), table2.columns].sum(axis=1)
        # table2['Всього'] = table2.apply(lambda row: row[table2.columns[table2.columns != 'Всього']].sum() if (row.index != '% підготовлених заїздів') | (row.index != 'Кількість заїздів всього') else None)
        table2['Всього'] = table2.loc[:, table2.columns != 'Всього'].sum(axis=1)
        # table2.loc['% підготовлених заїздів', 'Всього'] = (table2.loc['Кількість Н-З, підготовлених завчасно', 'Всього'] * 100 / table2.loc['Кількість заїздів по запису', 'Всього']).round(2)
        table2 = table2.reset_index()
        table2 = table2.rename(columns={'index': 'Менеджер'})

        table2 = table2.iloc[:5].append(table2.iloc[2], ignore_index=True).append(table2.iloc[5:], ignore_index=True)
        table2 = table2.drop(2, axis=0)
        table2.index = [0, 1, 2, 3, 4, 5]
        table2.loc[1, table2.columns != 'Менеджер'] = 0
        table2.loc[3, table2.columns != 'Менеджер'] = 0

        records = records.drop('Менеджер', axis=1)
    

    analytics_customer = records.copy()
    analytics_customer.insert(0, 'ПІБ', main['ПІБ'])
    analytics_customer.insert(1, 'Держ. номер', main['Держ. номер'])
    analytics_customer.insert(2, 'Заявка ТО', main['Заявка ТО'])
    if value_record == 'За записом':
        cols = ['ПІБ', 'Заявка ТО', 'Держ. номер', 'Коефіцієнт ефективності', 'Шлях клієнта з запису, діб', 'Тривалість візиту, години', 'Клієнт очікує призначеної дати візиту, діб']
    elif value_record == 'Без запису':
        cols = ['ПІБ', 'Заявка ТО', 'Держ. номер', 'Коефіцієнт ефективності', 'Тривалість візиту, години']
    analytics_customer.drop('Категорія', axis=1, inplace=True)

    # print(analytics_customer.columns[~analytics_customer.columns.isin(['ПІБ', 'Телефон', 'Держ. номер', 'Марка і модель'])])
          
    # r = analytics_customer[analytics_customer.columns[~analytics_customer.columns.isin(['ПІБ', 'Телефон', 'Держ. номер', 'Марка і модель'])]].isnull().any(axis=1)
    
    r = analytics_customer.isnull().any(axis=1)

    f = analytics_customer[~r]
    t = analytics_customer[r]

    analytics_customer = pd.concat([f, t])
        
    for c in analytics_customer.columns:
        if c == 'Коефіцієнт ефективності':
            analytics_customer[c] = analytics_customer[c].round(2)
        elif c == 'Шлях клієнта з запису, діб':
            analytics_customer[c] = analytics_customer[c].round(1)
        elif c == 'Тривалість візиту, години':
            analytics_customer[c] = analytics_customer[c].round(1)
        elif c == 'Клієнт очікує призначеної дати візиту, діб':
            analytics_customer[c] = analytics_customer[c].round(1)
        elif c not in cols:
            analytics_customer[c] = (analytics_customer[c]).apply(np.ceil)
            # analytics_customer[c] = analytics_customer[c].apply(lambda x: "{:,}".format(x)).replace('\.0$', '', regex=True)
            # analytics_customer[c] = analytics_customer[c].replace('nan', '', regex=True)
    
    # analytics_customer = analytics_customer.fillna('-')

    if value_record == 'За записом':
        main = main[['ПІБ', 'Телефон', 'Держ. номер', 'Марка і модель', 'Вхідний дзвінок', 'Втрачений дзвінок', 
                    'Створення запис на СТО', 'Створення ЗН', 'Плановий заїзд', 'Заїзд на парковку', 'Заїзд в зону сервісу',
                    'Виїзд з зони сервісу', 'Закриття ЗН', 'Виїзд з території']]
        
        r = main[['Марка і модель', 'Вхідний дзвінок', 'Втрачений дзвінок', 
                    'Створення запис на СТО', 'Створення ЗН', 'Плановий заїзд', 'Заїзд на парковку', 'Заїзд в зону сервісу',
                    'Виїзд з зони сервісу', 'Закриття ЗН', 'Виїзд з території']].isnull().any(axis=1)
        f = main[~r]
        t = main[r]

        main = pd.concat([f, t])

        main = main.fillna('-')


    elif value_record == 'Без запису':
        main = main[['ПІБ', 'Телефон', 'Держ. номер', 'Марка і модель', 'Створення ЗН', 
                     'Заїзд на парковку', 'Заїзд в зону сервісу',
                    'Виїзд з зони сервісу', 'Закриття ЗН', 'Виїзд з території']]
        
        r = main[['Марка і модель', 'Створення ЗН', 'Заїзд на парковку', 'Заїзд в зону сервісу',
                    'Виїзд з зони сервісу', 'Закриття ЗН', 'Виїзд з території']].isnull().any(axis=1)
        f = main[~r]
        t = main[r]

        main = pd.concat([f, t])

        main = main.fillna('-')

    if value_record == 'За записом':
       
        table1 = record_mean_areas.reset_index()[
            [
                'Показник', 'Клієнт очікує призначеної дати візиту, діб', 'Шлях клієнта з запису, діб', 
                'Тривалість візиту, години', 'Коефіцієнт ефективності'
            ]
        ]

        table3 = record_mean_areas[record_mean_areas['Показник'].isin(['Середнє', 'Мінімальне', 'Максимальне'])].reset_index()[
            [
                'Показник', 'Підготовка до візиту', 'Прийомка', 
                'Очікування ремонту', 'Ремонт загальний', 'Видача', 
                'Очікування в ремзоні (простої)', 
                'Перебування авто після завершення ремонту'
            ]
        ]
    elif value_record == 'Без запису':
        table1 = without_record_mean_areas.reset_index()[
            [
                'Показник', 'Клієнт очікує призначеної дати візиту, діб', 'Шлях клієнта з запису, діб', 
                'Тривалість візиту, години', 'Коефіцієнт ефективності'
            ]
        ]

        table3 = without_record_mean_areas[without_record_mean_areas['Показник'].isin(['Середнє', 'Мінімальне', 'Максимальне'])].reset_index()[
            [
                'Показник', 'Підготовка до візиту', 'Прийомка', 
                'Очікування ремонту', 'Ремонт загальний', 'Видача', 
                'Очікування в ремзоні (простої)', 
                'Перебування авто після завершення ремонту'
            ]
        ]

    return table1, table2, table3, main, describe_areas, analytics_customer


def get_gantt(analytics_customer_gantt):

    contents = []
    for _, row in analytics_customer_gantt.iterrows():
        fig = go.Figure()

        for task in ['Прийом автомобіля %', 'Ремонт %', 'Видача автомобіля %']:
            duration = row[task]

            fig.add_trace(go.Bar(
                x=[duration],
                y=[row['ПІБ']],
                # base=[0, 0],
                name=task,
                orientation='h',
                width=0.5,
                text=[str(duration) + '%'],
                textposition='auto',
            ))

        fig.update_layout(
            barmode='stack',
            xaxis=dict(
                title='Відсоток',
                range=[0, 100],
            ),
            yaxis=dict(title='Клієнт'),
            height=500,
        )

        content = dcc.Graph(
            figure=fig
        )
       
        contents.append(content)
    
    return [contents]