import warnings
import pandas as pd

pd.options.mode.chained_assignment = None

from tqdm import tqdm
import sys
import yaml
import json
import xmltodict
import numpy as np
from abc import ABC
from pathlib import Path
from datetime import datetime
from functools import lru_cache

sys.path.append( str( Path( __file__ ).absolute().parents[ 2 ] ) )

from modules.db import psql



def _prepare( db, start_date, end_date ):    

    # to = db.fetch_dataframe(
    #     f'''
    #     SELECT *
    #     FROM "TO"
    #     WHERE "TO"."Дата відкриття" >= TO_DATE('{start_date}', 'YYYY-MM-DD') AND "TO"."Дата відкриття" <= TO_DATE('{end_date}', 'YYYY-MM-DD');
    #     '''
    # )

    # cto = db.fetch_dataframe(
    #     f'''
    #     SELECT * 
    #     FROM "CTO"
    #     WHERE "CTO"."Плановий заїзд" >= TO_DATE('{start_date}', 'YYYY-MM-DD') AND "CTO"."Плановий заїзд" <= TO_DATE('{end_date}', 'YYYY-MM-DD');

    #     '''
    # )

    phones = db.fetch_dataframe(
        f'''
        SELECT * 
        FROM "phones"
        WHERE "phones"."callDate" >= TO_DATE('{start_date}', 'YYYY-MM-DD') AND "phones"."callDate" <= TO_DATE('{end_date}', 'YYYY-MM-DD');
        '''
    )

    traffic = db.fetch_dataframe(
        f'''
        SELECT * 
        FROM "traffic"
        WHERE "traffic"."Период" >= TO_DATE('{start_date}', 'YYYY-MM-DD') AND "traffic"."Период" <= TO_DATE('{end_date}', 'YYYY-MM-DD');
        '''
    )

    joined = db.fetch_dataframe(
                    f'''
                    SELECT t."ID" AS "ID ТО", t."Заявка ТО" AS "Заявка ТО", t.Клієнт, t."Держ. номер", t.Авто, t."Дата відкриття", t."Дата закриття", t."Проведення ЗН", t."Дата початку робіт", t.Нормогодини, t.Категорія, t.Менеджер,
                    ct."ID" AS "ID CTO", ct."Заявка ТО" AS "Заявка ТО з СТО", ct."Створення запис на СТО", ct."Плановий заїзд", ct."Планове закінчення",
                    CASE WHEN ct."ID" IS NULL THEN FALSE ELSE TRUE END AS "Запис"
                    FROM "TO" AS t
                    LEFT JOIN "CTO" AS ct ON t."ID" = ct."Заявка ТО"
                    WHERE t."Дата відкриття" >= TO_DATE('{start_date}', 'YYYY-MM-DD') AND t."Дата відкриття" <= TO_DATE('{end_date}', 'YYYY-MM-DD');
                    '''
                )

    # joined.to_csv('joined.csv', index=False)
    # exit()
    if len( joined ) == 0:
        return None

    joined['Створення запис на СТО'] = pd.to_datetime(joined['Створення запис на СТО'], format='%Y-%m-%d %H:%M:%S')
    joined[['Клієнт', 'Держ. номер', 'Авто']] = joined[['Клієнт', 'Держ. номер', 'Авто']].astype(str).apply(lambda x: x.str.strip())


    main = pd.DataFrame(
        index=joined.index,
        columns=['ПІБ', 'Телефон', 'Держ. номер', 'Марка і модель', 'Вхідний дзвінок', 'Втрачений дзвінок', 'Створення запис на СТО', \
                 'Створення ЗН', 'Плановий заїзд', 'Проведення ЗН', 'Дата початку робіт', 'Заїзд на парковку', 'Заїзд в зону сервісу', \
                 'Виїзд з зони сервісу', 'Дата закінчення робіт', 'Планове закінчення', 'Закриття ЗН', 'Виїзд з території', 
                 'Нормогодини', 'Категорія', 'Менеджер', 'Заявка ТО', 'Запис']
        )
    
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
    # main['Дата початку робіт'] = joined['Дата початку робіт']
    main['Заїзд на парковку'] = None
    main['Заїзд в зону сервісу'] = None
    main['Виїзд з зони сервісу'] = None
    # main['Дата закінчення робіт'] = joined['Дата закінчення робіт']
    main['Планове закінчення'] = joined['Планове закінчення']
    main['Закриття ЗН'] = joined['Дата закриття']
    main['Виїзд з території'] = None
    main['Нормогодини'] = joined['Нормогодини']
    main['Категорія'] = joined['Категорія']
    main['Менеджер'] = joined['Менеджер']
    main['Заявка ТО'] = joined['Заявка ТО']
    main['Запис'] = joined['Запис']
    main['Запис'] = main['Запис'].astype(bool)
    

    for i, row in tqdm(joined.iterrows()):
        # try:

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
            first_incoming_call = pd.to_datetime(first_incoming_phones['callDate'], format='%Y-%m-%d %H:%M:%S')
            # call_duration = int(first_incoming_phones['tellTime'])
            call_duration = pd.to_numeric(first_incoming_phones['tellTime'], errors='coerce')
            first_incoming_index = first_incoming_call.searchsorted(row['Створення запис на СТО'])
            # first_incoming_index = int(str(first_incoming_index).replace(',', ''))

            if len(first_incoming_call):
                if first_incoming_index == len(first_incoming_call):
                    first_incoming_index = first_incoming_index - 1
                # print(str(call_duration.iloc[first_incoming_index]).replace('\\xa', ''))
                try:
                    main.loc[i, ['Вхідний дзвінок']] = first_incoming_call.iloc[first_incoming_index] - pd.Timedelta(int(str(call_duration.iloc[first_incoming_index]).replace('\\xa', '')), 'sec')
                    incoming_client_number = first_incoming_phones['phone'].iloc[first_incoming_index]
                    first_incoming = True
                except:
                    pass
                    

            # отримуємо перший втрачений дзвінок за три дні до запису
            # можливо треба виправити віднімання 3х днів від зати запису, щоб захватити більше дзвінків 
            # використати np.floor()
            missed_phones = phones[
                    (phones['client'].str.strip() == row['Клієнт'].strip()) & (phones['callType'] == 'Вхідний') & ((phones['status'] == 'NO_ANSWER') | \
                            (phones['status'] == 'NOT WORKING TIME')) & (row['Створення запис на СТО'] - pd.Timedelta(3, 'd') < \
                                phones['callDate']) & (phones['callDate'] < row['Створення запис на СТО'])]
            missed_call = pd.to_datetime(missed_phones['callDate'], format='%Y-%m-%d %H:%M:%S')
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
            #     incoming_call = pd.to_datetime(incoming_phones['callDate'], format='%Y-%m-%d %H:%M:%S')
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

                    
            traffic_row = traffic[(traffic['ГосударственныйНомер'] == row['Держ. номер'])]
            if len(traffic_row):
                closest_id = traffic_row['Период'].searchsorted(pd.to_datetime(row['Дата відкриття'], format='%Y-%m-%d %H:%M:%S'))
                if closest_id == len(traffic_row):
                    closest_id = closest_id - 1
                id_race = traffic_row.iloc[closest_id]['ИдентификаторЗаезда']
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
                entering_service = entering_service.iloc[0]
                main.loc[i, ['Заїзд в зону сервісу']] = entering_service


            departure_service = pd.to_datetime(
                traffic[
                    (traffic['ГосударственныйНомер'] == row['Держ. номер']) & ((traffic['ИдентификаторЗоны1'] == 'Service exit') | \
                        (traffic['ИдентификаторЗоны1'] == 'Service (in/out) Camera 1') | (traffic['ИдентификаторЗоны1'] == 'Service (in/out) Camera 2')) & \
                            (traffic['ИдентификаторЗаезда'] == id_race)]['ДатаНачала'],
                format='%Y.%m.%d %H:%M:%S')
            
            if len(departure_service):
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
    
        # except:
        #     continue

    # main['Вхідний дзвінок'] = pd.to_datetime(main['Вхідний дзвінок'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    # main['Втрачений дзвінок'] = pd.to_datetime(main['Втрачений дзвінок'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    # main['Створення запис на СТО'] = pd.to_datetime(main['Створення запис на СТО'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    # main['Створення ЗН'] = pd.to_datetime(main['Створення ЗН'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    # main['Плановий заїзд'] = pd.to_datetime(main['Плановий заїзд'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    # main['Заїзд на парковку'] = pd.to_datetime(main['Заїзд на парковку'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    # main['Заїзд в зону сервісу'] = pd.to_datetime(main['Заїзд в зону сервісу'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    # main['Виїзд з зони сервісу'] = pd.to_datetime(main['Виїзд з зони сервісу'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    # main['Закриття ЗН'] = pd.to_datetime(main['Закриття ЗН'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')
    # main['Виїзд з території'] = pd.to_datetime(main['Виїзд з території'], format='%Y-%m-%d %H:%M:%S').dt.strftime('%d.%m.%Y %H:%M:%S').replace('T', '')

    # print(main)
    # main.to_csv('stages.csv', index=False)

    # print(main)
    # main.to_csv('main.csv', index=False)
    # exit()

    return main

def _get_prepare(
        db: psql.PostgreSQLDB,
        freq,
        start_date,
        end_date,
    ):

    stages_main = pd.DataFrame(
        columns = [
            "ПІБ", "Телефон", "Держ. номер", "Марка і модель", "Вхідний дзвінок", "Втрачений дзвінок", "Створення запис на СТО",
            "Створення ЗН", "Плановий заїзд", "Проведення ЗН", "Дата початку робіт", "Заїзд на парковку", "Заїзд в зону сервісу",
            "Виїзд з зони сервісу", "Дата закінчення робіт", "Планове закінчення", "Закриття ЗН", "Виїзд з території", "Нормогодини",
            "Категорія", "Менеджер", "Заявка ТО", "Запис"
        ]
    )
    stages_main['Запис'] = stages_main['Запис'].astype(bool)
    # start_date = '2023-07-02'
    # end_date = '2023-07-03'
    date_range = pd.date_range(start=start_date, end=end_date, freq=freq)

    for start, end in tqdm(zip(date_range, date_range[1:])):
        # try:

            start = start.date()
            end = end.date()

            print(f'Отримуємо дані з {start} по {end}')

            stages = _prepare( db, start, end )
            
            if stages is None:
                continue

            stages_main = pd.concat([stages_main, stages])
        # except:
        #     print(f'Помилка при отриманні даних з {start} по {end}')

    stages_main = stages_main.drop_duplicates()


    return stages_main

# prepare( '2023-01-01', '2023-02-01' )

class CronjobKyivStages( ABC ):
    def update(
        self,
        db: psql.PostgreSQLDB,
        start_date: str,
        end_date: str,
    ):
        
        # start_date = pd.to_datetime( start_date ).date()
        # end_date = pd.to_datetime( end_date ).date()

        stages = db.fetch_dataframe( f'SELECT * FROM "stages"' )

        update = True

        if len( stages ) == 0:
            print( f'No data found in "stages"' )
    
            to = db.fetch_dataframe('SELECT "Дата відкриття" FROM "TO"')
            if len( to ) > 0:
                open_date = pd.to_datetime( to[ 'Дата відкриття' ] )
            else:
                print( f'Database is empty!' )
                return None
            # start_date = open_date.min().date()
            start_date = pd.to_datetime('2023-01-01').date()
            end_date = open_date.max().date()
        
            stages1 = _get_prepare( db, 'MS', start_date, end_date )
            start = pd.to_datetime(stages1[ 'Створення ЗН' ]).max().date() + pd.Timedelta(1, "d")
            stages2 = _get_prepare(db,  'D', start, end_date )
            stages = pd.concat([stages1, stages2])
        else:
            stages[ 'Створення ЗН' ] = pd.to_datetime( stages[ 'Створення ЗН' ] )
            start = stages[ 'Створення ЗН' ].max().date() + pd.Timedelta(1, "d")

            to = db.fetch_dataframe('SELECT "Дата відкриття" FROM "TO"')
            if len( to ) > 0:
                open_date = pd.to_datetime( to[ 'Дата відкриття' ] )
            else:
                print( f'Database is empty!' )
                # треба додати видалення таблиці або інші варіанти
                return None
            
            end = open_date.max().date()

            if start > end:
                print('Data is up to date in "stages"')
                update = False
            else:
                stages = _get_prepare( db, 'D', start, end )


        stages = stages.drop_duplicates()
        # stages['Дата початку робіт'] = stages['Дата початку робіт'].fillna('0001-01-01 00:00:00')
        # stages['Дата закінчення робіт'] = stages['Дата закінчення робіт'].fillna('0001-01-01 00:00:00')
        # stages['Планове закінчення'] = stages['Планове закінчення'].fillna('0001-01-01 00:00:00')
        # stages['Закриття ЗН'] = stages['Закриття ЗН'].fillna('0001-01-01 00:00:00')
        # stages['Виїзд з території'] = stages['Виїзд з території'].fillna('0001-01-01 00:00:00')
        # stages['Заїзд на парковку'] = stages['Заїзд на парковку'].fillna('0001-01-01 00:00:00')
        # stages['Виїзд з зони сервісу'] = stages['Виїзд з зони сервісу'].fillna('0001-01-01 00:00:00')
        # stages['Виїзд з території'] = stages['Виїзд з території'].fillna('0001-01-01 00:00:00')

        stages[[
            'Вхідний дзвінок',
            'Втрачений дзвінок',
            'Створення запис на СТО',
            'Створення ЗН',
            'Плановий заїзд',
            'Проведення ЗН',
            'Дата початку робіт',
            'Заїзд на парковку',
            'Заїзд в зону сервісу',
            'Виїзд з зони сервісу',
            'Дата закінчення робіт',
            'Планове закінчення',
            'Закриття ЗН',
            'Виїзд з території'
            ]] = stages[[
            'Вхідний дзвінок',
            'Втрачений дзвінок',
            'Створення запис на СТО',
            'Створення ЗН',
            'Плановий заїзд',
            'Проведення ЗН',
            'Дата початку робіт',
            'Заїзд на парковку',
            'Заїзд в зону сервісу',
            'Виїзд з зони сервісу',
            'Дата закінчення робіт',
            'Планове закінчення',
            'Закриття ЗН',
            'Виїзд з території'
            ]].fillna('0001-01-01 00:00:00')

        stages.to_csv('stages.csv', index=False)

        if len( stages ) > 0 and update:
            db.insert_dataframe( '"stages"', stages )
            
            
        #     if start > end_date:
        #         print('Data is up to date in "stages"')
        #         update = False
        #     else:
        #         stages = _get_prepare( db, 'D', start, end_date )

        # if len( stages ) > 0 and update:
        #     db.insert_dataframe( '"stages"', stages )


def update(
    db_config_path = 'configs/local.yaml',
    start_date = pd.to_datetime('2023-01-01').date(),
    end_date = datetime.now().date(),
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

    adapter = CronjobKyivStages()
    adapter.update(
        db,
        start_date,
        end_date
    )

update()