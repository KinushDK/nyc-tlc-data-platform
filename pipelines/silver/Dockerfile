FROM apache/spark-py:v3.4.0

USER root

# Install boto3 for any S3 interactions outside of Spark's own connector
RUN pip install boto3

# Copy the transformation script into the image
COPY transform_yellow.py /opt/spark/work-dir/transform_yellow.py

USER spark

WORKDIR /opt/spark/work-dir