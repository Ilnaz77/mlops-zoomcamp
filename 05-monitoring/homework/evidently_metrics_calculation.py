import datetime
import time
import random
import logging
import uuid
import pytz
import pandas as pd
import io
import psycopg
import joblib

from prefect import task, flow
from prefect.artifacts import create_markdown_artifact
from datetime import date
from evidently.report import Report
from evidently import ColumnMapping
from evidently.metrics import ColumnCorrelationsMetric, ColumnQuantileMetric

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

SEND_TIMEOUT = 10
rand = random.Random()

create_table_statement = """
drop table if exists dummy_metrics;
create table dummy_metrics(
	timestamp timestamp,
	current_quantile float,
	diff_corr_pred_total_amount float
)
"""

begin = datetime.datetime(2023, 3, 1, 0, 0)

raw_data = pd.read_parquet('data/green_tripdata_2023-03.parquet')
reference_data = pd.read_parquet('data/reference.parquet')

with open('models/lin_reg.bin', 'rb') as f_in:
    model = joblib.load(f_in)


num_features = ['passenger_count', 'trip_distance', 'fare_amount', 'total_amount']
cat_features = ['PULocationID', 'DOLocationID']
column_mapping = ColumnMapping(
    prediction='prediction',
    numerical_features=num_features,
    categorical_features=cat_features,
    target=None
)

report = Report(metrics=[
    ColumnQuantileMetric(column_name="fare_amount", quantile=0.5),
    ColumnCorrelationsMetric(column_name="prediction")
]
)


@task(retries=2, retry_delay_seconds=5, name="db preparation")
def prep_db():
    with psycopg.connect("host=localhost port=5431 user=postgres password=example", autocommit=True) as conn:
        res = conn.execute("SELECT 1 FROM pg_database WHERE datname='test'")
        if len(res.fetchall()) == 0:
            conn.execute("create database test;")
        with psycopg.connect("host=localhost port=5431 dbname=test user=postgres password=example") as conn:
            conn.execute(create_table_statement)


@task(retries=2, retry_delay_seconds=5, name="calculate metrics")
def calculate_metrics_postgresql(curr, i):
    current_data = raw_data[(raw_data.lpep_pickup_datetime >= (begin + datetime.timedelta(i))) &
                            (raw_data.lpep_pickup_datetime < (begin + datetime.timedelta(i + 1)))]

    # current_data.fillna(0, inplace=True)
    current_data['prediction'] = model.predict(current_data[num_features + cat_features].fillna(0))

    report.run(reference_data=reference_data,
               current_data=current_data,
               column_mapping=column_mapping)

    result = report.as_dict()

    current_quantile = result['metrics'][0]['result']['current']['value']
    reference_quantile = result['metrics'][0]['result']['reference']['value']

    curr_corr_prediction_and_total_amount = result['metrics'][1]['result']['current']['pearson']['values']['y'][3]
    ref_corr_prediction_and_total_amount = result['metrics'][1]['result']['reference']['pearson']['values']['y'][3]

    diff_corr = curr_corr_prediction_and_total_amount - ref_corr_prediction_and_total_amount

    curr.execute(
        "insert into dummy_metrics(timestamp, current_quantile, diff_corr_pred_total_amount) values (%s, %s, %s)",
        (begin + datetime.timedelta(i), current_quantile, diff_corr)
    )

    return current_quantile


@flow(retries=2, name="batch_monitoring_backfill")
def batch_monitoring_backfill():
    list_of_q = []
    prep_db()
    last_send = datetime.datetime.now() - datetime.timedelta(seconds=10)
    with psycopg.connect("host=localhost port=5431 dbname=test user=postgres password=example",
                         autocommit=True) as conn:
        for i in range(0, 31):
            with conn.cursor() as curr:
                current_q = calculate_metrics_postgresql(curr, i)
                list_of_q.append(current_q)

            # new_send = datetime.datetime.now()
            # seconds_elapsed = (new_send - last_send).total_seconds()
            # if seconds_elapsed < SEND_TIMEOUT:
            #     time.sleep(SEND_TIMEOUT - seconds_elapsed)
            # while last_send < new_send:
            #     last_send = last_send + datetime.timedelta(seconds=10)
            # logging.info("data sent")

    markdown_report = f"""# Quantile Report

            ## Summary

            Duration Prediction 

            ## Max Q_0.5 in Current data (March 2023 Green)

            | Region    | Max Qunatile |
            |:----------|-------:|
            | {date.today()} | {max(list_of_q):.2f} |
            """

    # create_markdown_artifact(
    #     key="05_monitoring-report", markdown=markdown_report
    # )


if __name__ == '__main__':
    batch_monitoring_backfill()
