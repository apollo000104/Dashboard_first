import warnings
import pandas as pd

pd.options.mode.chained_assignment = None

import json
import xmltodict
import numpy as np
from functools import lru_cache


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

@lru_cache(maxsize=None)
def get(value_record, value_section, start_date, end_date):
    print(value_record, value_section, start_date, end_date)
    phones = pd.read_json('data/phones.json')

    with open('data/new/Трафик', 'r') as f:
        traffic_raw = f.read()
        # to_raw = BeautifulSoup(to_raw, 'xml')
        traffic_raw = xmltodict.parse(traffic_raw)
        traffic_raw = json.dumps(traffic_raw, ensure_ascii=False)
        traffic_raw = json.loads(traffic_raw)
        traffic_raw = traffic_raw['soap:Envelope']['soap:Body']['m:GetTrafficDataResponse']['m:return']['ЗаписьТрафика']
        traffic_raw = pd.DataFrame(traffic_raw)
        traffic_raw = traffic_raw.replace('0001-01-01T00:00:00', np.nan)
        traffic = traffic_raw.copy()
        # traffic = traffic.rename(columns={'ГосударственныйНомер': 'Держ. номер'})
        # traffic_raw = traffic_raw.replace('T', ' ')

    with open('data/new/ЗаявкаТО', 'r') as f:
        to_raw = f.read()
        # to_raw = BeautifulSoup(to_raw, 'xml')
        to_raw = xmltodict.parse(to_raw)
        to_raw = json.dumps(to_raw, ensure_ascii=False)
        to_raw = json.loads(to_raw)
        to_raw = to_raw['soap:Envelope']['soap:Body']['m:GetDocumentsListResponse']['m:return']['ЗаявкаТО']
        to_raw = pd.DataFrame(to_raw)
        to_raw = to_raw.replace('0001-01-01T00:00:00', np.nan)
        to = to_raw.copy()

    with open('data/new/ЗаписНаСТО', 'r') as f:
        cto_raw = f.read()
        # cto_raw = BeautifulSoup(cto_raw, 'xml')
        cto_raw = xmltodict.parse(cto_raw)
        cto_raw = json.dumps(cto_raw, ensure_ascii=False)
        cto_raw = json.loads(cto_raw)
        cto_raw = cto_raw['soap:Envelope']['soap:Body']['m:GetDocumentsListResponse']['m:return']['ЗаписьНаСТО']
        cto_raw = pd.DataFrame(cto_raw)
        cto_raw = cto_raw.replace('0001-01-01T00:00:00', np.nan)
        cto = cto_raw.copy()

    phones['callDate'] = pd.to_datetime(phones['callDate'], format='%d.%m.%Y %H:%M:%S')
    # traffic['Период'] = pd.to_datetime(traffic_raw['Период'], format='%d.%m.%Y %H:%M:%S')
    traffic['Период'] = pd.to_datetime(traffic_raw['Период'], format='%Y%m%d %H:%M:%S')
    traffic = traffic.sort_values('Период')

    # Додати фільтр по категоріям
    # to = to[to['Категорія'].isin(['Вст. дод. обладнання. (Оплачувана)', 'Вст. дод. обладнання. докомплектація (НЕ оплачується.)', \
    #                               'Гарантія оплачувана', 'Клієнт оплачувана', 'Кузовний ремонт']) == True]
    # to = to[(to['Держ. номер'] != '-') & (to['Держ. номер'].notna() == True)]
    # ids = [i.text for i in to_raw.find_all('УИД')]

    # В майбутньому перевіряти статус РОБІТ

    to['ID'] = to['ДокументID'].str['УИД']
    to['Заявка ТО'] = to['ДокументID'].str['Номер'] 
    to['Дата відкриття'] = pd.to_datetime(to['ДатаОткрытия'], format='%Y-%m-%d %H:%M:%S')
    to['Дата закриття'] = pd.to_datetime(to['ДатаЗакрытия'], format='%Y-%m-%d %H:%M:%S')
    to['Проведення ЗН'] = pd.to_datetime(to['ДатаЗаезда'], format='%Y-%m-%d %H:%M:%S')

    to['Клієнт'] = to['Клиент'].str['Наименование']
    to['Держ. номер'] = to['Авто'].str['ГосНомер']
    to['Авто'] = to['Авто'].str['Наименование']
    to['Нормогодини'] = to['ТаблицаРабот'].apply(lambda row: _calculate(row))
    to['Категорія'] = to['Категория']
    to['Дата початку робіт'] = to['МаршрутЗаявки'].apply(lambda x: _application_route_start(x))
    to['Дата закінчення робіт'] = to['МаршрутЗаявки'].apply(lambda x: _application_route_end(x))

    to = to[['ID', 'Заявка ТО', 'Клієнт', 'Держ. номер', 'Авто', 'Дата відкриття', 'Дата закриття', 'Проведення ЗН', 'Дата початку робіт', 'Дата закінчення робіт', 'Нормогодини', 'Категорія']].copy()
    to = to.set_index('ID')


    cto['ID'] = cto['ЗаявкаТО'].str['ДокументID'].str['УИД']
    cto['Створення запис на СТО'] = pd.to_datetime(cto['ДокументID'].str['Дата'], format='%Y-%m-%d %H:%M:%S')
    cto['Плановий заїзд'] = pd.to_datetime(cto['ДатаНачала'], format='%Y-%m-%d %H:%M:%S')
    cto['Планове закінчення'] = pd.to_datetime(cto['ДатаОкончания'], format='%Y-%m-%d %H:%M:%S')

    cto = cto[['ID', 'Створення запис на СТО', 'Плановий заїзд', 'Планове закінчення']].copy()
    cto = cto.set_index('ID')

    # try to use left joind when we will have заявка то in запис на СТО
    if value_record == 'За записом':
        joined = to.join(cto, lsuffix='ТО', rsuffix='СТО', on=['ID'], how='inner')
    elif value_record == 'Без запису':
        joined = to.join(cto, lsuffix='ТО', rsuffix='СТО', on=['ID'], how='left')
        joined = joined[joined['Створення запис на СТО'].isna() == True]
    
    # joined = joined[joined['За записом'] == APPOINTMENT[value_record]]
    joined = joined[(joined['Дата відкриття'].dt.date >= pd.to_datetime(start_date, format='%Y-%m-%d')) & (joined['Дата відкриття'].dt.date <= pd.to_datetime(end_date, format='%Y-%m-%d'))]
    joined[['Клієнт', 'Держ. номер', 'Авто']] = joined[['Клієнт', 'Держ. номер', 'Авто']].astype(str).apply(lambda x: x.str.strip())
    # joined.to_csv('test.csv')

    main = pd.DataFrame(
        index=joined.index,
        columns=['ПІБ', 'Телефон', 'Держ. номер', 'Марка і модель', 'Вхідний дзвінок', 'Втрачений дзвінок', 'Створення запис на СТО', \
                 'Створення ЗН', 'Плановий заїзд', 'Проведення ЗН', 'Дата початку робіт', 'Заїзд на парковку', 'Заїзд в зону сервісу', \
                 'Виїзд з зони сервісу', 'Дата закінчення робіт', 'Планове закінчення', 'Закриття ЗН', 'Виїзд з території', 
                 'Нормогодини', 'Категорія'])
    
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
        
        # incoming_call не зовсім incoming
        # може бути ситуація, коли клієнт зателефонував у не робочий час
        # і йому передзвонили та зробили запис на СТО
        # тобто фіксування ймовірного запису
        incoming_phones = phones[
                (phones['client'] == row['Клієнт']) & (phones['status'] == 'ANSWERED') & (phones['callDate'] < row['Створення запис на СТО'] + pd.Timedelta(5, 'm'))]
        incoming_call = pd.to_datetime(incoming_phones['callDate'], format='%d.%m.%Y %H:%M:%S')
        call_duration = incoming_phones['tellTime']
        incoming_index = incoming_call.searchsorted(row['Створення запис на СТО'])

        if len(incoming_call):
            # if row['Клієнт'] == 'Мартинюк Микола Миколайович':
            #     print(incoming_call)
            #     print(incoming_index)
            #     print(row['Створення запис на СТО'])
            if incoming_index == len(incoming_call):
                incoming_index = incoming_index - 1
            main.loc[i, ['Вхідний дзвінок']] = incoming_call.iloc[incoming_index] - pd.Timedelta(int(call_duration.iloc[incoming_index]), 'sec')
            incoming_client_number = incoming_phones['phone'].iloc[incoming_index]

        # if row['Клієнт'] == 'Сандирєв Данило Леонідович':
        #     print(incoming_call)
        #     print(incoming_index)
                

        # отримуємо перший втрачений дзвінок за три дні до запису
        # можливо треба виправити віднімання 3х днів від зати запису, щоб захватити більше дзвінків 
        # використати np.floor()
        missed_phones = phones[
                (phones['client'] == row['Клієнт']) & (phones['callType'] == 'Вхідний') & ((phones['status'] == 'NO_ANSWER') | \
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
            # if row['Держ. номер'] == 'КА4155НВ':
            #     print(pd.to_datetime(row['Дата відкриття'], format='%d.%m.%Y %H:%M:%S'))
            #     print(traffic_row)
            #     print(closest_id)
            #     print(traffic_row.iloc[closest_id]['ИдентификаторЗаезда'])
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

        # if row['Клієнт'] == 'Авраменко Андрій Володимирович':
        #     print(main[main['ПІБ'] == 'Авраменко Андрій Володимирович'])
        #     main[main['ПІБ'] == 'Авраменко Андрій Володимирович'].to_csv('testsssss.csv')
    
            
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

    print(main)

    if value_section != 'Всі':
        # main = main[main['Категорія'].isin(AREAS[value_section])].apply(np.ceil)
        main = main[main['Категорія'].isin(AREAS[value_section])]
    else:
        # main = main.apply(np.ceil)
        main = main


    if value_record == 'За записом':
        record_analytics_mean = pd.DataFrame(
            columns = [
                'Обробка втраченого звінка', 'Контакт з клієнтом', 'Шлях клієнта з першого контакту', 'Шлях клієнта з запису', 'Підготовка до візиту', 
                'Очікування прийому', 'Прийомка', 'Очікування ремонту', 'Ремонт загальний', 'Ремонт відсканований', 
                'Очікування в ремзоні (простої)', 'Видача', 'Перебування авто після завершення ремонту', 'Тривалість візиту', 
                'Клієнт очікує призначеної дати візиту, годин', 'Відхилення від запланованого часу прибуття клієнта', 
                'Коефіцієнт ефективності'
            ]
        )

        record_analytics_mean['Клієнт очікує призначеної дати візиту, годин'] = abs(pd.to_datetime(main['Створення ЗН'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Створення запис на СТО'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 3600
        record_analytics_mean['Обробка втраченого звінка'] = abs(pd.to_datetime(main['Вхідний дзвінок'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Втрачений дзвінок'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Контакт з клієнтом'] = abs(pd.to_datetime(main['Створення запис на СТО'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Вхідний дзвінок'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Шлях клієнта з першого контакту'] = (abs(pd.to_datetime(main['Виїзд з території'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Вхідний дзвінок'], format='%d.%m.%Y %H:%M:%S')) - abs(pd.to_datetime(main['Створення ЗН'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Створення запис на СТО'], format='%d.%m.%Y %H:%M:%S'))).dt.total_seconds() / 60
        record_analytics_mean['Шлях клієнта з запису'] = (abs(pd.to_datetime(main['Виїзд з території'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Плановий заїзд'], format='%d.%m.%Y %H:%M:%S'))).dt.total_seconds() / 60
        record_analytics_mean['Підготовка до візиту'] = (pd.to_datetime(main['Плановий заїзд'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Створення ЗН'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Очікування прийому'] = (pd.to_datetime(main['Проведення ЗН'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Прийомка'] = (pd.to_datetime(main['Заїзд в зону сервісу'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Створення ЗН'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Очікування ремонту'] = (pd.to_datetime(main['Заїзд в зону сервісу'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Проведення ЗН'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Ремонт загальний'] = abs(pd.to_datetime(main['Виїзд з зони сервісу'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд в зону сервісу'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        # record_analytics_mean['Ремонт відсканований'] = (pd.to_datetime(main['Дата закінчення робіт'], format='%Y.%m.%d %H:%M:%S') - pd.to_datetime(main['Дата початку робіт'], format='%Y.%m.%d %H:%M:%S')).dt.total_seconds / 60
        record_analytics_mean['Ремонт відсканований'] = 0
        # record_analytics_mean['Очікування в ремзоні (простої)'] = record_analytics_mean['Ремонт загальний'] - record_analytics_mean['Ремонт відсканований']
        record_analytics_mean['Очікування в ремзоні (простої)'] = 0
        record_analytics_mean['Видача'] = abs(pd.to_datetime(main['Закриття ЗН'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Виїзд з зони сервісу'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Перебування авто після завершення ремонту'] = (pd.to_datetime(main['Виїзд з території'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Закриття ЗН'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Тривалість візиту'] = abs(pd.to_datetime(main['Виїзд з території'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 3600
        record_analytics_mean['Відхилення від запланованого часу прибуття клієнта'] = abs(pd.to_datetime(main['Плановий заїзд'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Коефіцієнт ефективності'] = (main['Нормогодини'] / record_analytics_mean['Ремонт загальний'])

        record_analytics_mean['Категорія'] = main['Категорія']

        if value_section != 'Всі':
            record_mean_areas = record_analytics_mean[record_analytics_mean['Категорія'].isin(AREAS[value_section])].describe().loc[['count', 'mean', 'min', 'max']].apply(np.ceil)
        else:
            record_mean_areas = record_analytics_mean.describe().loc[['count', 'mean', 'min', 'max']].apply(np.ceil)
        record_mean_areas = record_mean_areas.rename(
            index={'count': 'Кількість', 'mean': 'Середнє', 'min': 'Мінімальне', 'max': 'Максимальне'}
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
                'Тривалість візиту', 'Коефіцієнт ефективності'
            ]
        )

        without_record_analytics_mean['Очікування клієнта в черзі'] = abs(pd.to_datetime(main['Створення ЗН'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        without_record_analytics_mean['Прийомка'] = (pd.to_datetime(main['Заїзд в зону сервісу'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Створення ЗН'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        without_record_analytics_mean['Очікування ремонту'] = (pd.to_datetime(main['Заїзд в зону сервісу'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Проведення ЗН'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        without_record_analytics_mean['Ремонт загальний'] = abs(pd.to_datetime(main['Виїзд з зони сервісу'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд в зону сервісу'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        # without_record_analytics_mean['Ремонт відсканований'] = (pd.to_datetime(main['Дата закінчення робіт'], format='%Y.%m.%d %H:%M:%S') - pd.to_datetime(main['Дата початку робіт'], format='%Y.%m.%d %H:%M:%S')).dt.total_seconds / 60
        without_record_analytics_mean['Ремонт відсканований'] = 0
        # without_record_analytics_mean['Очікування в ремзоні (простої)'] = without_record_analytics_mean['Ремонт загальний'] - without_record_analytics_mean['Ремонт відсканований']
        without_record_analytics_mean['Очікування в ремзоні (простої)'] = 0
        without_record_analytics_mean['Видача'] = abs(pd.to_datetime(main['Закриття ЗН'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Виїзд з зони сервісу'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        without_record_analytics_mean['Перебування авто після завершення ремонту'] = (pd.to_datetime(main['Виїзд з території'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Закриття ЗН'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        without_record_analytics_mean['Тривалість візиту'] = abs(pd.to_datetime(main['Виїзд з території'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        without_record_analytics_mean['Коефіцієнт ефективності'] = (main['Нормогодини'] / without_record_analytics_mean['Ремонт загальний'])
        without_record_analytics_mean['Категорія'] = main['Категорія']

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

    analytics_customer = records.copy()
    analytics_customer.insert(0, 'ПІБ', main['ПІБ'])
    analytics_customer.insert(1, 'Телефон', main['Телефон'])
    analytics_customer.insert(2, 'Держ. номер', main['Держ. номер'])
    analytics_customer.insert(3, 'Марка і модель', main['Марка і модель'])
    analytics_customer.drop('Категорія', axis=1, inplace=True)

    # print(analytics_customer.columns[~analytics_customer.columns.isin(['ПІБ', 'Телефон', 'Держ. номер', 'Марка і модель'])])
          
    # r = analytics_customer[analytics_customer.columns[~analytics_customer.columns.isin(['ПІБ', 'Телефон', 'Держ. номер', 'Марка і модель'])]].isnull().any(axis=1)
    
    r = analytics_customer.isnull().any(axis=1)

    f = analytics_customer[~r]
    t = analytics_customer[r]

    analytics_customer = pd.concat([f, t])

    for c in analytics_customer.columns:
        if c not in ['ПІБ', 'Телефон', 'Держ. номер', 'Марка і модель']:
            analytics_customer[c] = (analytics_customer[c]).apply(np.ceil)
            # analytics_customer[c] = analytics_customer[c].apply(lambda x: "{:,}".format(x)).replace('\.0$', '', regex=True)
            analytics_customer[c] = analytics_customer[c].replace('nan', '', regex=True)
    
    analytics_customer = analytics_customer.fillna('-')
    analytics_customer.loc[len(analytics_customer) + 1] = pd.Series([' '] * len(analytics_customer.columns))
    analytics_customer.loc[len(analytics_customer) + 1] = pd.Series([' '] * len(analytics_customer.columns))

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
    
    # describe_areas.to_csv('describe_mean.csv')
    # main.to_csv('main.csv')
    # analytics_customer.to_csv('analytics_customer.csv')


    return main, describe_areas, analytics_customer

get("За записом", "Всі", "2023-01-01", "2023-01-28")