import os
import pickle

import mlflow
from mlflow.tracking import MlflowClient
from flask import Flask, request, jsonify

os.environ["AWS_ACCESS_KEY_ID"] = ""
os.environ["AWS_SECRET_ACCESS_KEY"] = ""
os.environ["MLFLOW_S3_ENDPOINT_URL"] = "https://storage.yandexcloud.net"

# RUN_ID = os.getenv('RUN_ID')  # можно сделать как переменную окружения
RUN_ID = "9fb826dfc09648f896d6771468f6015e"

mlflow.set_tracking_uri("http://158.160.110.3:5000")
logged_model = f'runs:/{RUN_ID}/model'
# logged_model = f's3://zoomcamp-mlops/web_services/3/{RUN_ID}/artifacts/model'  # тогда не нужен set_tracking_uri
model = mlflow.pyfunc.load_model(logged_model)


def prepare_features(ride):
    features = {}
    features['PU_DO'] = '%s_%s' % (ride['PULocationID'], ride['DOLocationID'])
    features['trip_distance'] = ride['trip_distance']
    return features


def predict(features):
    preds = model.predict(features)
    return float(preds[0])


app = Flask('duration-prediction')


@app.route('/predict', methods=['POST'])
def predict_endpoint():
    ride = request.get_json()

    features = prepare_features(ride)
    pred = predict(features)

    result = {
        'duration': pred,
        'model_version': RUN_ID
    }

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=9696)
