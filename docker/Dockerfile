FROM ubuntu:16.04

RUN apt update && apt -y install python3-pip git

RUN pip3 install flask-restful requests gunicorn python-bitcoinlib

RUN git clone https://github.com/Utrum/hodl-api.git

#RUN 
