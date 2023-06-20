FROM svizor/zoomcamp-model:mlops-3.10.0-slim

RUN pip install -U pip
RUN pip install pipenv

WORKDIR /app

COPY [ "Pipfile", "Pipfile.lock", "./" ]

RUN pipenv install --system --deploy

COPY [ "starter.py", "./" ]

ENTRYPOINT ["python","./starter.py"]


# docker build -t ride-duration-prediction-homework:v2 .
# docker run -it --rm ride-duration-prediction-homework:v2 year month AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY