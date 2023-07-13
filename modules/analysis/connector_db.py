import warnings
import pandas as pd

pd.options.mode.chained_assignment = None

import sys
import yaml
import json
import xmltodict
import numpy as np
from pathlib import Path
from functools import lru_cache

import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, Input, Output, State, dash_table

sys.path.append( str( Path( __file__ ).absolute().parents[ 2 ] ) )

from modules.db import psql

AREAS = {
    'Зона ТО і ремонту': ('Клієнт оплачувана', 'Гарантія оплачувана'),
    'Малярно-кузовна дільниця': ('Кузовний ремонт'),
    'Дільниця додаткового обладнання': ('Вст. дод. обладнання. (Оплачувана)', 'Вст. дод. обладнання. докомплектація (НЕ оплачується.)')
}

APPOINTMENT = {
    'За записом': 'True',
    'Без запису': 'False'
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
def get( value_record, value_section, value_manager, start_date, end_date ):
    # print(value_record, value_section, value_manager, start_date, end_date)

    db_config_path = '/Users/aleksandrlozko/stages-customer-service-dashboard-atollhoding1/configs/local.yaml'
    with open( db_config_path, 'r' ) as f:
        db_config = yaml.safe_load( f )

    db = psql.PostgreSQLDB(
        host=db_config[ 'host' ],
        port=db_config[ 'port' ],
        type=db_config[ 'type' ],
        db=db_config[ 'db' ],
        credentials=db_config[ 'credentials' ],
    )

    main = db.fetch_dataframe(
        f'''
        SELECT *
        FROM "stages"
        WHERE "Створення ЗН" >= TO_DATE('{start_date}', 'YYYY-MM-DD') AND "Створення ЗН" <= TO_DATE('{end_date}', 'YYYY-MM-DD') AND "Запис" IS {APPOINTMENT[value_record]};
        '''
    )

    main['Вхідний дзвінок'] = main['Вхідний дзвінок'].str.replace("0001-01-01 00:00:00", 'None')
    main['Вхідний дзвінок'] = pd.to_datetime(main['Вхідний дзвінок'])
    # main['Вхідний дзвінок'] = pd.to_datetime(main['Вхідний дзвінок'], errors='coerce').replace(pd.Timestamp('0001-01-01 00:00:00'), pd.NaT)

    print(main)
    main.to_csv('new_maon.csv', index=False)

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

        record_analytics_mean['Клієнт очікує призначеної дати візиту, діб'] = abs(pd.to_datetime(main['Плановий заїзд'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Створення запис на СТО'], format='%Y-%m-%d %H:%M:%S')).dt.total_seconds() / 86400
        # record_analytics_mean['Обробка втраченого звінка'] = abs(pd.to_datetime(main['Вхідний дзвінок'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Втрачений дзвінок'], format='%Y-%m-%d %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Контакт з клієнтом'] = abs(pd.to_datetime(main['Створення запис на СТО'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Вхідний дзвінок'], format='%Y-%m-%d %H:%M:%S')).dt.total_seconds() / 60
        # record_analytics_mean['Шлях клієнта з першого контакту'] = (abs(pd.to_datetime(main['Виїзд з території'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Вхідний дзвінок'], format='%Y-%m-%d %H:%M:%S')) - abs(pd.to_datetime(main['Створення ЗН'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Створення запис на СТО'], format='%Y-%m-%d %H:%M:%S'))).dt.total_seconds() / 60
        record_analytics_mean['Шлях клієнта з запису, діб'] = (abs(pd.to_datetime(main['Виїзд з території'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Плановий заїзд'], format='%Y-%m-%d %H:%M:%S'))).dt.total_seconds() / 86400
        record_analytics_mean['Підготовка до візиту'] = (pd.to_datetime(main['Плановий заїзд'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Створення ЗН'], format='%Y-%m-%d %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['У т. ч. очікування прийому'] = (pd.to_datetime(main['Проведення ЗН'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%Y-%m-%d %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Прийомка'] = (pd.to_datetime(main['Заїзд в зону сервісу'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%Y-%m-%d %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Очікування ремонту'] = (pd.to_datetime(main['Заїзд в зону сервісу'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Проведення ЗН'], format='%Y-%m-%d %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Ремонт загальний'] = abs(pd.to_datetime(main['Виїзд з зони сервісу'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Заїзд в зону сервісу'], format='%Y-%m-%d %H:%M:%S')).dt.total_seconds() / 60
        # record_analytics_mean['Ремонт відсканований'] = (pd.to_datetime(main['Дата закінчення робіт'], format='%Y.%m.%d %H:%M:%S') - pd.to_datetime(main['Дата початку робіт'], format='%Y.%m.%d %H:%M:%S')).dt.total_seconds / 60
        record_analytics_mean['Ремонт відсканований'] = 0
        # record_analytics_mean['Очікування в ремзоні (простої)'] = record_analytics_mean['Ремонт загальний'] - record_analytics_mean['Ремонт відсканований']
        record_analytics_mean['Очікування в ремзоні (простої)'] = 0
        record_analytics_mean['Видача'] = abs(pd.to_datetime(main['Закриття ЗН'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Виїзд з зони сервісу'], format='%Y-%m-%d %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Перебування авто після завершення ремонту'] = (pd.to_datetime(main['Виїзд з території'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Закриття ЗН'], format='%Y-%m-%d %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Тривалість візиту, години'] = abs(pd.to_datetime(main['Виїзд з території'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%Y-%m-%d %H:%M:%S')).dt.total_seconds() / 3600
        # record_analytics_mean['Відхилення від запланованого часу прибуття клієнта'] = abs(pd.to_datetime(main['Плановий заїзд'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%Y-%m-%d %H:%M:%S')).dt.total_seconds() / 60
        record_analytics_mean['Коефіцієнт ефективності'] = (main['Нормогодини'] / (record_analytics_mean['Ремонт загальний'] / 60)).round(2)
        # record_analytics_mean['Коефіцієнт ефективності'] = record_analytics_mean['Коефіцієнт ефективності'].astype('object')
        # record_analytics_mean['Нормогодини'] = main['Нормогодини']
        record_analytics_mean['Менеджер'] = main['Менеджер']

        record_analytics_mean['Категорія'] = main['Категорія']

        record_mean_areas = record_analytics_mean.describe().loc[['count', 'mean', 'min', 'max']].apply(np.ceil)
        record_mean_areas = record_mean_areas.rename(
            index={'count': 'Кількість, заїзди', 'mean': 'Середнє', 'min': 'Мінімальне', 'max': 'Максимальне'}
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

        without_record_analytics_mean['Очікування клієнта в черзі'] = abs(pd.to_datetime(main['Створення ЗН'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%Y-%m-%d %H:%M:%S')).dt.total_seconds() / 60
        without_record_analytics_mean['Прийомка'] = (pd.to_datetime(main['Заїзд в зону сервісу'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%Y-%m-%d %H:%M:%S')).dt.total_seconds() / 60
        without_record_analytics_mean['Очікування ремонту'] = (pd.to_datetime(main['Заїзд в зону сервісу'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Проведення ЗН'], format='%Y-%m-%d %H:%M:%S')).dt.total_seconds() / 60
        without_record_analytics_mean['Ремонт загальний'] = abs(pd.to_datetime(main['Виїзд з зони сервісу'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Заїзд в зону сервісу'], format='%Y-%m-%d %H:%M:%S')).dt.total_seconds() / 60
        # without_record_analytics_mean['Ремонт відсканований'] = (pd.to_datetime(main['Дата закінчення робіт'], format='%Y.%m.%d %H:%M:%S') - pd.to_datetime(main['Дата початку робіт'], format='%Y.%m.%d %H:%M:%S')).dt.total_seconds / 60
        without_record_analytics_mean['Ремонт відсканований'] = 0
        # without_record_analytics_mean['Очікування в ремзоні (простої)'] = without_record_analytics_mean['Ремонт загальний'] - without_record_analytics_mean['Ремонт відсканований']
        without_record_analytics_mean['Очікування в ремзоні (простої)'] = 0
        without_record_analytics_mean['Видача'] = abs(pd.to_datetime(main['Закриття ЗН'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Виїзд з зони сервісу'], format='%Y-%m-%d %H:%M:%S')).dt.total_seconds() / 60
        without_record_analytics_mean['Перебування авто після завершення ремонту'] = (pd.to_datetime(main['Виїзд з території'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Закриття ЗН'], format='%Y-%m-%d %H:%M:%S')).dt.total_seconds() / 60
        without_record_analytics_mean['Тривалість візиту, години'] = abs(pd.to_datetime(main['Виїзд з території'], format='%Y-%m-%d %H:%M:%S') - pd.to_datetime(main['Заїзд на парковку'], format='%Y-%m-%d %H:%M:%S')).dt.total_seconds() / 3600
        without_record_analytics_mean['Коефіцієнт ефективності'] = (main['Нормогодини'] / (without_record_analytics_mean['Ремонт загальний'] / 60)).round(2)
        without_record_analytics_mean['Категорія'] = main['Категорія']
        without_record_analytics_mean['Менеджер'] = main['Менеджер']

        # просто для groupby
        without_record_analytics_mean['Підготовка до візиту'] = 0
        without_record_analytics_mean['Клієнт очікує призначеної дати візиту, діб'] = 0
        without_record_analytics_mean['Шлях клієнта з запису, діб'] = 0

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
        print(table2)

        # to['Дата відкриття'] = pd.to_datetime(to['Дата відкриття'], format='%Y-%m-%d %H:%M:%S')

        # all_rec = to[(to['Дата відкриття'].dt.date >= pd.to_datetime(start_date, format='%Y-%m-%d')) & (to['Дата відкриття'].dt.date <= pd.to_datetime(end_date, format='%Y-%m-%d'))].groupby('Менеджер').agg(
        #     all=('Менеджер', 'count')
        # ).reset_index()
        # all_rec = all_rec.rename(columns={'all': 'Кількість заїздів всього'})
        # not_all_rec = all_rec[~all_rec['Менеджер'].isin(list(table2['Менеджер']))]
        # all_rec = all_rec[all_rec['Менеджер'].isin(list(table2['Менеджер']))]
        # new_rec = pd.Series([all_rec['Кількість заїздів всього'].sum()] + all_rec['Кількість заїздів всього'].to_list())

        new_rec = db.fetch_dataframe(
            f'''
            SELECT COALESCE("Менеджер", 'Загальне') AS "Менеджер", COUNT(*) AS "Кількість заїздів всього"
            FROM "TO"
            WHERE "Дата відкриття" >= TO_DATE('{start_date}', 'YYYY-MM-DD') AND "Дата відкриття" <= TO_DATE('{end_date}', 'YYYY-MM-DD')
            GROUP BY ROLLUP("Менеджер");
            '''
        )
        print(new_rec)
        exit()

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

        # to['Дата відкриття'] = pd.to_datetime(to['Дата відкриття'], format='%Y-%m-%d %H:%M:%S')
        # all_rec = to[(to['Дата відкриття'].dt.date >= pd.to_datetime(start_date, format='%Y-%m-%d')) & (to['Дата відкриття'].dt.date <= pd.to_datetime(end_date, format='%Y-%m-%d'))].groupby('Менеджер').agg(
        #     all=('Менеджер', 'count')
        # ).reset_index()
        # all_rec = all_rec.rename(columns={'all': 'Кількість заїздів всього'})
        # all_rec = all_rec[all_rec['Менеджер'].isin(list(table2['Менеджер']))]
        # new_rec = pd.Series([all_rec['Кількість заїздів всього'].sum()] + all_rec['Кількість заїздів всього'].to_list())

        new_rec = db.fetch_dataframe(
            f'''
            SELECT COALESCE("Менеджер", 'Загальне') AS "Менеджер", COUNT(*) AS "Кількість заїздів всього"
            FROM "TO"
            WHERE "Дата відкриття" >= TO_DATE('{start_date}', 'YYYY-MM-DD') AND "Дата відкриття" <= TO_DATE('{end_date}', 'YYYY-MM-DD')
            GROUP BY ROLLUP("Менеджер");
            '''
        )

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

get('За записом', 'Всі', 'Всі', '2023-02-01', '2023-03-01' )
exit()
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