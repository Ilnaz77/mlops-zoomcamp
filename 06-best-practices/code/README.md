## Code snippets

### Building and running Docker images

```bash
docker build -t stream-model-duration:v2 .
```

```bash
docker run -it --rm \
    -p 8080:8080 \
    -e MODEL_BUCKET="zoomcamp-mlops" \
    -e MLFLOW_EXPERIMENT_ID="4" \
    -e RUN_ID="f8fd04f838554ea8b14d8d264090ecd3" \
    -e KINESIS_PREDICTIONS_STREAM_NAME="best-practices-06-stream-output" \
    -e KINESIS_REGION_NAME="ru-central1" \
    -e KINESIS_ENDPOINT_URL="https://yds.serverless.yandexcloud.net" \
    -e KINESIS_PREDICTIONS_CLOUD_NAME="b1gfe9noiorfsvs06hgu" \
    -e KINESIS_PREDICTIONS_DB_NAME="etnqhldvb6j1qqjt6nol" \
    -e AWS_SECRET_ACCESS_KEY="YCPUfjxRS1nLsNVBI-x2VfAEH6RUUO5leO5ijGt6" \
    -e AWS_ACCESS_KEY_ID="YCAJEZ8oYIJdSI_4eRuAt5UQq" \
    -e TRACKING_SERVER_HOST="158.160.110.3" \
    -e MLFLOW_S3_ENDPOINT_URL=https://storage.yandexcloud.net \
    -e TEST_RUN="True" \
    stream-model-duration:v2
```

Mounting the model folder:

```
docker run -it --rm \
    -p 8080:8080 \
    -e PREDICTIONS_STREAM_NAME="ride_predictions" \
    -e RUN_ID="Test123" \
    -e MODEL_LOCATION="/app/model" \
    -e TEST_RUN="True" \
    -e AWS_DEFAULT_REGION="eu-west-1" \
    -v $(pwd)/model:/app/model \
    stream-model-duration:v2
```

### Specifying endpoint URL

```bash
aws --endpoint-url=http://localhost:4566 \
    kinesis list-streams
```

```bash
aws --endpoint-url=http://localhost:4566 \
    kinesis create-stream \
    --stream-name ride_predictions \
    --shard-count 1
```

#### Дернуть данные из стрима (после отработки докера)
```bash
aws  --endpoint-url=http://localhost:4566 \
    kinesis     get-shard-iterator \
    --shard-id 'shardId-000000000000' \
    --shard-iterator-type TRIM_HORIZON \
    --stream-name 'ride_predictions' \
    --query 'ShardIterator'
```

```bash
RESULT=$(aws --endpoint-url=http://localhost:4566 kinesis get-records --shard-iterator $SHARD_ITERATOR)
echo ${RESULT} | jq -r '.Records[0].Data' | base64 --decode
```

### Unable to locate credentials

If you get `'Unable to locate credentials'` error, add these
env variables to the `docker-compose.yaml` file:

```yaml
- AWS_ACCESS_KEY_ID=abc
- AWS_SECRET_ACCESS_KEY=xyz
```

### Make

Without make:

```
isort .
black .
pylint --recursive=y .
pytest tests/
```

With make:

```
make quality_checks
make test
```


To prepare the project, run

```bash
make setup
```


### IaC
w/ Terraform

#### Setup

**Installation**:

* [aws-cli](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) (both versions are fine)
* [terraform client](https://www.terraform.io/downloads)

**Configuration**:

1. If you've already created an AWS account, head to the IAM section, generate your secret-key, and download it locally.
[Instructions](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-prereqs.html)

2. [Configure]((https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html)) `aws-cli` with your downloaded AWS secret keys:
      ```shell
         $ aws configure
         AWS Access Key ID [None]: xxx
         AWS Secret Access Key [None]: xxx
         Default region name [None]: eu-west-1
         Default output format [None]:
      ```

3. Verify aws config:
      ```shell
        $ aws sts get-caller-identity
      ```

4. (Optional) Configuring with `aws profile`: [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sourcing-external.html) and [here](https://registry.terraform.io/providers/hashicorp/aws/latest/docs#using-an-external-credentials-process)

<br>

#### Execution


1. To create infra (manually, in order to test on staging env)
    ```shell
    # Initialize state file (.tfstate)
    terraform init

    # Check changes to new infra plan
    terraform plan -var-file=vars/stg.tfvars
    ```

    ```shell
    # Create new infra
    terraform apply -var-file=vars/stg.tfvars
    ```

2. To prepare aws env (copy model artifacts, set env-vars for lambda etc.):
    ```
    . ./scripts/deploy_manual.sh
    ```

3. To test the pipeline end-to-end with our new cloud infra:
    ```
    . ./scripts/test_cloud_e2e.sh
    ```

4. And then check on CloudWatch logs. Or try `get-records` on the `output_kinesis_stream` (refer to `integration_test`)

5. Destroy infra after use:
    ```shell
    # Delete infra after your work, to avoid costs on any running services
    terraform destroy
    ```

<br>

### CI/CD

1. Create a PR (feature branch): `.github/workflows/ci-tests.yml`
    * Env setup, Unit test, Integration test, Terraform plan
2. Merge PR to `develop`: `.github/workflows/cd-deploy.yml`
    * Terraform plan, Terraform apply, Docker build & ECR push, Update Lambda config

### Notes

* Unfortunately, the `RUN_ID` (if set via the `ENV` or `ARG` in `Dockerfile`), disappears during lambda invocation.
We'll set it via `aws lambda update-function-configuration` CLI command (refer to `deploy_manual.sh` or `.github/workflows/cd-deploy.yml`)
