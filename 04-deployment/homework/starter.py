#!/usr/bin/env python
# coding: utf-8
import pickle
import sys
import os
import pandas as pd
import boto3

os.environ["AWS_ACCESS_KEY_ID"] = str(sys.argv[3])
os.environ["AWS_SECRET_ACCESS_KEY"] = str(sys.argv[4])
os.environ["AWS_ENDPOINT_URL"] = "https://storage.yandexcloud.net"
os.environ["AWS_DEFAULT_REGION"] = "ru-central1-a"

with open('model.bin', 'rb') as f_in:
    dv, model = pickle.load(f_in)

categorical = ['PULocationID', 'DOLocationID']


def load_to_s3(output_file, year, month):
    session = boto3.session.Session()
    s3 = session.client(
        service_name='s3',
        endpoint_url='https://storage.yandexcloud.net'
    )

    s3.upload_file(output_file, 'zoomcamp-mlops', f'yellow-{year:04d}-{month:02d}.parquet')


def read_data(filename):
    df = pd.read_parquet(filename)

    df['duration'] = df.tpep_dropoff_datetime - df.tpep_pickup_datetime
    df['duration'] = df.duration.dt.total_seconds() / 60

    df = df[(df.duration >= 1) & (df.duration <= 60)].copy()

    df[categorical] = df[categorical].fillna(-1).astype('int').astype('str')

    return df


def read_data_and_apply_model(input_file, output_file, year, month):
    df = read_data(input_file)

    dicts = df[categorical].to_dict(orient='records')
    X_val = dv.transform(dicts)
    y_pred = model.predict(X_val)

    print(y_pred.mean())

    df['ride_id'] = f'{year:04d}/{month:02d}_' + df.index.astype('str')

    df_result = pd.DataFrame()
    df_result['ride_id'] = df['ride_id']
    df_result['predicted_duration'] = y_pred

    df_result.to_parquet(
        output_file,
        engine='pyarrow',
        compression=None,
        index=False
    )

    load_to_s3(output_file, year, month)


def main(year, month):
    taxi_type = "yellow"
    input_file = f'https://d37ci6vzurychx.cloudfront.net/trip-data/{taxi_type}_tripdata_{year:04d}-{month:02d}.parquet'
    output_file = f'{taxi_type}-{year:04d}-{month:02d}.parquet'

    read_data_and_apply_model(input_file, output_file, year, month)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
