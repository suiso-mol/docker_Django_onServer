FROM python:3.9-buster
ENV PYTHONUNBUFFERED 1
ENV http_proxy http://192.50.200.3:8080/
ENV https_proxy http://192.50.200.3:8080/
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . /code/
