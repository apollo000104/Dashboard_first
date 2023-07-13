import warnings
import pandas as pd

pd.options.mode.chained_assignment = None

import json
import numpy as np
from datetime import datetime
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

@lru_cache(maxsize=None)
def get(value_record, value_section, start_date, end_date):
    print(value_record, value_section, start_date, end_date)
    phones = pd.read_json('data/phones.json')
    traffic = pd.read_excel('data/traffic.xlsx', header=3)
    to_raw = pd.read_excel('data/заявка то.xls')
    cto_raw = pd.read_excel('data/запис на сто.xls')

    phones['callDate'] = pd.to_datetime(phones['callDate'], format='%d.%m.%Y %H:%M:%S')

    traffic_columns = traffic.iloc[0]
    traffic = traffic[traffic[traffic.columns[0]].isin(['out', 'in']) == True]
    # traffic = traffic[traffic['out'].notna() == True]
    traffic.columns = traffic_columns
    traffic['Период'] = pd.to_datetime(traffic['Период'], format='%d.%m.%Y %H:%M:%S')
    traffic = traffic.sort_values('Период')
    
    to = to_raw[to_raw['Закрита'].notna() == True]
    to = to[to['Категорія'].isin(['Вст. дод. обладнання. (Оплачувана)', 'Вст. дод. обладнання. докомплектація (НЕ оплачується.)', \
                                  'Гарантія оплачувана', 'Клієнт оплачувана', 'Кузовний ремонт']) == True]
    to = to[(to['Держ. номер'] != '-') & (to['Держ. номер'].notna() == True)]
    to['Відкрита'] = pd.to_datetime(to['Відкрита'], format='%d.%m.%Y %H:%M:%S')
    to['Закрита'] = pd.to_datetime(to['Закрита'], format='%d.%m.%Y %H:%M:%S')
    to['Відкрита str'] = to['Відкрита'].dt.date.astype('str')
    to['ID'] = to['Держ. номер'] + '_' + to['Менеджер'] + '_' + to['Відкрита str']
    to = to[['ID', 'Клієнт', 'Номер', 'Держ. номер', 'Авто', 'Відкрита', 'Закрита', 'Сума', 'VIN', 'За записом', 'Категорія', 'Пост']].copy()

    cto = cto_raw[(cto_raw['Статус'] == 'Виконана') & (cto_raw['Клієнт'] != 'Новый клиент')]
    cto['Дата'] = pd.to_datetime(cto['Дата'], format='%d.%m.%Y %H:%M:%S')
    cto['Дата початку'] = pd.to_datetime(cto['Дата початку'], format='%d.%m.%Y %H:%M:%S')
    cto['Дата закінчення'] = pd.to_datetime(cto['Дата закінчення'], format='%d.%m.%Y %H:%M:%S')
    cto['Дата початку str'] = cto['Дата початку'].dt.date.astype('str')
    cto['ID'] = cto['Держ. номер'] + '_' + cto['Менеджер'] + '_' + cto['Дата початку str']
    cto = cto[['ID', 'Дата', 'Дата початку', 'Дата закінчення', 'Менеджер']].copy()

    # try to use left joind when we will have заявка то in запис на СТО
    if value_record == 'За записом':
        to = to.set_index('ID')
        cto = cto.set_index('ID')
        joined = to.join(cto, lsuffix='ТО', rsuffix='СТО', on=['ID'], how='inner')
    elif value_record == 'Без запису':
        to = to[~(to['ID'].isin(cto['ID']))]
        to = to.set_index('ID')
        cto = cto.set_index('ID')
        joined = to.join(cto, lsuffix='ТО', rsuffix='СТО', on=['ID'], how='left')
    
    # to = to.set_index('ID')
    # cto = cto.set_index('ID')

    # joined = to.join(cto, lsuffix='ТО', rsuffix='СТО', on=['ID'], how='inner')
    # joined.to_csv('test.csv')
    
    joined = joined[joined['За записом'] == APPOINTMENT[value_record]]
    joined = joined[(joined['Відкрита'].dt.date >= pd.to_datetime(start_date, format='%Y-%m-%d')) & (joined['Відкрита'].dt.date <= pd.to_datetime(end_date, format='%Y-%m-%d'))]
    joined[['Клієнт', 'Держ. номер', 'Авто']] = joined[['Клієнт', 'Держ. номер', 'Авто']].apply(lambda x: x.str.strip())

    main = pd.DataFrame(
        index=joined.index,
        columns=['ПІБ', 'Телефон', 'Держ. номер', 'Марка і модель', 'Вхідний дзвінок', 'Втрачений дзвінок', 'Створення запис на СТО', \
                 'Створення ЗН', 'Плановий заїзд', 'Заїзд на парковку', 'Заїзд в зону сервісу', 'Виїзд з зони сервісу', \
                 'Закінчення запису на СТО', 'Закриття ЗН', 'Виїзд з території', 'Категорія'])
    
    main['ПІБ'] = joined['Клієнт']
    main['Телефон'] = None
    main['Держ. номер'] = joined['Держ. номер']
    main['Марка і модель'] = joined['Авто']
    main['Вхідний дзвінок'] = None
    main['Втрачений дзвінок'] = None
    main['Створення запис на СТО'] = joined['Дата']
    main['Плановий заїзд'] = joined['Дата початку']
    main['Закінчення запису на СТО'] = joined['Дата закінчення']
    main['Створення ЗН'] = joined['Відкрита']
    main['Заїзд на парковку'] = None
    main['Заїзд в зону сервісу'] = None
    main['Виїзд з зони сервісу'] = None
    main['Закриття ЗН'] = joined['Закрита']
    main['Виїзд з території'] = None
    # main['Дата початку'] = joined['Відкрита']
    main['Категорія'] = joined['Категорія']
    # main['Дата початку'] = joined['Дата початку']

    for i, row in joined.iterrows():

        incoming_client_number = None
        missed_client_number = None
        
        # incoming_call не зовсім incoming
        # може бути ситуація, коли клієнт зателефонував у не робочий час
        # і йому передзвонили та зробили запис на СТО
        # тобто фіксування ймовірного запису
        incoming_phones = phones[
                (phones['client'] == row['Клієнт']) & (phones['status'] == 'ANSWERED') & (phones['callDate'] < row['Дата'] + pd.Timedelta(5, 'm'))]
        incoming_call = pd.to_datetime(incoming_phones['callDate'], format='%d.%m.%Y %H:%M:%S')
        call_duration = incoming_phones['tellTime']
        incoming_index = incoming_call.searchsorted(row['Дата'])
        if len(incoming_call):
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
                        (phones['status'] == 'NOT WORKING TIME')) & (row['Дата'] - pd.Timedelta(3, 'd') < \
                            phones['callDate']) & (phones['callDate'] < row['Дата'])]
        missed_call = pd.to_datetime(missed_phones['callDate'], format='%d.%m.%Y %H:%M:%S')
        if len(missed_call):
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

        traffic_row = traffic[(traffic['Держ. номер'] == row['Держ. номер'])]
        if len(traffic_row):
            closest_id = traffic_row['Период'].searchsorted(pd.to_datetime(row['Відкрита'], format='%d.%m.%Y %H:%M:%S'))
            if closest_id == len(traffic_row):
                closest_id = closest_id - 1
            id_race = traffic_row.iloc[closest_id]['Ід Заїзду']
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
                (traffic['Держ. номер'] == row['Держ. номер']) & ((traffic['Ід1'] == 'Main Entrance Terminal') | \
                    (traffic['Ід1'] == 'Main Entrance Camera') | (traffic['Ід1'] == 'Service exit')) & \
                        (traffic['Ід2'] == 'Город') & (traffic['Ід Заїзду'] == id_race)]['Д 1'],
            format='%d.%m.%Y %H:%M:%S')

        if len(entering_parking):
            if len(entering_parking) > 1:
                entering_parking = entering_parking.iloc[-1]
            else:
                entering_parking = entering_parking.iloc[0]
            main.loc[i, ['Заїзд на парковку']] = entering_parking


        entering_service =pd.to_datetime(
            traffic[
                ((traffic['Держ. номер'] == row['Держ. номер']) & (traffic['Ід Заїзду'] == id_race) & \
                    ((traffic['Ід1'] == 'Main Entrance Terminal') | (traffic['Ід1'] == 'Main Entrance Camera') | \
                    (traffic['Ід1'] == 'Service (in/out) Camera 1') | (traffic['Ід1'] == 'Service (in/out) Camera 2')) & \
                        ((traffic['Ід2'] == 'Service (in/out) Camera 1') | (traffic['Ід2'] == 'Service (in/out) Camera 2') | \
                         (traffic['Ід2'] == 'Service In Camera')))]['Период'], 
            format='%d.%m.%Y %H:%M:%S')
    

        if len(entering_service):
            # if len(entering_service) > 1:
            #     entering_service = entering_service.iloc[-1]
            # else:
            entering_service = entering_service.iloc[0]
            main.loc[i, ['Заїзд в зону сервісу']] = entering_service


        departure_service = pd.to_datetime(
            traffic[
                (traffic['Держ. номер'] == row['Держ. номер']) & ((traffic['Ід1'] == 'Service exit') | \
                    (traffic['Ід1'] == 'Service (in/out) Camera 1') | (traffic['Ід1'] == 'Service (in/out) Camera 2')) & \
                        (traffic['Ід Заїзду'] == id_race)]['Д 1'],
            format='%d.%m.%Y %H:%M:%S')
        
        if len(departure_service):
            # if len(departure_service) > 1:
            #     departure_service_list.append(departure_service.iloc[0])
            # else:
                # departure_service = departure_service.iloc[0]
                main.loc[i, ['Виїзд з зони сервісу']] = departure_service.iloc[-1]


        departure_parking = pd.to_datetime(
            traffic[
                (traffic['Держ. номер'] == row['Держ. номер']) & ((traffic['Ід1'] == 'Main Entrance Terminal') | \
                    (traffic['Ід1'] == 'Main Entrance Camera') | (traffic['Ід1'] == 'Service (in/out) Camera 1') | \
                        (traffic['Ід1'] == 'Service (in/out) Camera 2') | (traffic['Ід1'] == 'Service exit')) & \
                        ((traffic['Ід2'] == 'Город') | (traffic['Ід2'] == 'Main Exit Camera')) & \
                            (traffic['Ід Заїзду'] == id_race)]['Период'], 
            format='%d.%m.%Y %H:%M:%S')
        if len(departure_parking):
            if len(departure_parking) > 1:
                 main.loc[i, ['Виїзд з території']] = departure_parking.iloc[-1]
            else:
                 main.loc[i, ['Виїзд з території']] = departure_parking.iloc[0]

            # print(main['Виїзд з території'].loc[i])
            # print(main['Заїзд на парковку'].loc[i])
            if str(main['Виїзд з території'].loc[i]) == str(main['Заїзд на парковку'].loc[i]):
                main.loc[i, ['Виїзд з території']] = main['Виїзд з зони сервісу'].loc[i]
    
            
    main['Вхідний дзвінок'] = pd.to_datetime(main['Вхідний дзвінок'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    main['Втрачений дзвінок'] = pd.to_datetime(main['Втрачений дзвінок'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    main['Створення запис на СТО'] = pd.to_datetime(main['Створення запис на СТО'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    main['Створення ЗН'] = pd.to_datetime(main['Створення ЗН'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    main['Плановий заїзд'] = pd.to_datetime(main['Плановий заїзд'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    main['Заїзд на парковку'] = pd.to_datetime(main['Заїзд на парковку'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    main['Заїзд в зону сервісу'] = pd.to_datetime(main['Заїзд в зону сервісу'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    main['Виїзд з зони сервісу'] = pd.to_datetime(main['Виїзд з зони сервісу'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    main['Закінчення запису на СТО'] = pd.to_datetime(main['Закінчення запису на СТО'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
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
                'Обробка втраченого звінка', 'Контакт з клієнтом', 'Шлях клієнта з першого контакту', 'Шлях клієнта з запису', 'Підготовка до візиту', 
                'Очікування прийому', 'Прийомка', 'Очікування ремонту', 'Ремонт загальний', 'Ремонт відсканований', 
                'Очікування в ремзоні (простої)', 'Видача', 'Перебування авто після завершення ремонту', 'Тривалість візиту', 
                'Клієнт очікує призначеної дати візиту, годин', 'Відхилення від запланованого часу прибуття клієнта', 
                'Коефіцієнт ефективності'
            ]
        )

        record_analytics_mean['Обробка втраченого звінка'] = abs(pd.to_datetime(main['Вхідний дзвінок'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Втрачений дзвінок'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Контакт з клієнтом'] = abs(pd.to_datetime(main['Створення запис на СТО'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Вхідний дзвінок'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Шлях клієнта з першого контакту'] = (abs(pd.to_datetime(main['Виїзд з території'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Вхідний дзвінок'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() - \
            abs(pd.to_datetime(main['Створення ЗН'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Створення запис на СТО'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds()) / 60
        record_analytics_mean['Шлях клієнта з запису'] = abs(pd.to_datetime(main['Виїзд з території'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Плановий заїзд'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Підготовка до візиту'] = (pd.to_datetime(main['Плановий заїзд'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Створення ЗН'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Очікування прийому'] = 0
        record_analytics_mean['Прийомка'] = (pd.to_datetime(main['Заїзд в зону сервісу'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Створення ЗН'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Очікування ремонту'] = 0
        record_analytics_mean['Ремонт загальний'] = abs(pd.to_datetime(main['Виїзд з зони сервісу'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд в зону сервісу'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Ремонт відсканований'] = 0
        record_analytics_mean['Очікування в ремзоні (простої)'] = 0
        record_analytics_mean['Видача'] = abs(pd.to_datetime(main['Закриття ЗН'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Виїзд з зони сервісу'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Перебування авто після завершення ремонту'] = (pd.to_datetime(main['Виїзд з території'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Закриття ЗН'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Тривалість візиту'] = abs(pd.to_datetime(main['Виїзд з території'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 3600
        record_analytics_mean['Клієнт очікує призначеної дати візиту, годин'] = abs(pd.to_datetime(main['Створення ЗН'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Створення запис на СТО'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 3600
        record_analytics_mean['Відхилення від запланованого часу прибуття клієнта'] = abs(pd.to_datetime(main['Плановий заїзд'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Коефіцієнт ефективності'] = 0

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
        without_record_analytics_mean['Очікування ремонту'] = 0
        without_record_analytics_mean['Ремонт загальний'] = abs(pd.to_datetime(main['Виїзд з зони сервісу'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд в зону сервісу'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        without_record_analytics_mean['Ремонт відсканований'] = 0
        without_record_analytics_mean['Очікування в ремзоні (простої)'] = 0
        without_record_analytics_mean['Видача'] = abs(pd.to_datetime(main['Закриття ЗН'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Виїзд з зони сервісу'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        without_record_analytics_mean['Перебування авто після завершення ремонту'] = (pd.to_datetime(main['Виїзд з території'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Закриття ЗН'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        without_record_analytics_mean['Тривалість візиту'] = abs(pd.to_datetime(main['Виїзд з території'], format='%d.%m.%Y %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%d.%m.%Y %H:%M:%S')).dt.total_seconds() / 60
        without_record_analytics_mean['Коефіцієнт ефективності'] = 0
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
            analytics_customer[c] = analytics_customer[c].apply(lambda x: "{:,}".format(x)).replace('\.0$', '', regex=True)
            analytics_customer[c] = analytics_customer[c].replace('nan', '', regex=True)
    
    analytics_customer = analytics_customer.fillna('-')
    analytics_customer.loc[len(analytics_customer) + 1] = pd.Series([' '] * len(analytics_customer.columns))
    # analytics_customer.loc[len(analytics_customer) + 1] = pd.Series([' '] * len(analytics_customer.columns))

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