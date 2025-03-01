import os
import sys

sys.path.append('../')
from datetime import datetime

import batch
import pandas as pd


def dt(hour, minute, second=0):
    return datetime(2022, 1, 1, hour, minute, second)


def create_prepare_data():
    data = [
        (None, None, dt(1, 2), dt(1, 10)),
        (1, None, dt(1, 2), dt(1, 10)),
        (1, 2, dt(2, 2), dt(2, 3)),
        (None, 1, dt(1, 2, 0), dt(1, 2, 50)),
        (2, 3, dt(1, 2, 0), dt(1, 2, 59)),
        (3, 4, dt(1, 2, 0), dt(2, 2, 1)),
    ]

    columns = ['PULocationID', 'DOLocationID', 'tpep_pickup_datetime', 'tpep_dropoff_datetime']
    df = pd.DataFrame(data, columns=columns)

    input_file = batch.get_input_path(2022, 1)

    df.to_parquet(
        input_file,
        engine='pyarrow',
        compression=None,
        index=False,
        storage_options=batch.options
    )


def run_check_the_correctness():
    os.system('python ../batch.py 2022 1')

    output_file = batch.get_output_path(2022, 1)

    df_actual = pd.read_parquet(output_file, storage_options=batch.options)

    print(round(df_actual['predicted_duration'].sum(), 2))


if __name__ == "__main__":
    create_prepare_data()
    run_check_the_correctness()
