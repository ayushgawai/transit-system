FROM apache/airflow:2.9.2

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    python3-dev \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Install Python dependencies first
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Install additional packages at build time (not runtime)
# Install in order to avoid conflicts
RUN pip install --no-cache-dir \
    kafka-python \
    confluent-kafka \
    boto3 \
    pyyaml \
    psycopg2-binary

# Install Snowflake packages
RUN pip install --no-cache-dir \
    apache-airflow-providers-snowflake==5.3.0 \
    snowflake-connector-python==3.6.0

# Install dbt packages last - let pip resolve compatible versions
RUN pip install --no-cache-dir \
    dbt-core \
    dbt-snowflake \
    dbt-redshift

