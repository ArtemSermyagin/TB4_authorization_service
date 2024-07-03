FROM python:3

WORKDIR /TB4_authorization_service

COPY ./requirements.txt /TB4_authorization_service/

RUN pip install -r requirements.txt

COPY . .

