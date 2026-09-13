FROM apache/spark-py:v3.4.0

USER root

RUN pip install boto3

# Add Hadoop-AWS and AWS SDK jars for S3A support
RUN curl -o /opt/spark/jars/hadoop-aws-3.3.4.jar \
    https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    curl -o /opt/spark/jars/aws-java-sdk-bundle-1.12.262.jar \
    https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar

COPY transform_yellow.py /opt/spark/work-dir/transform_yellow.py

USER spark

WORKDIR /opt/spark/work-dir