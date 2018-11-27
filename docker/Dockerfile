FROM ubuntu:16.04

RUN apt update && apt -y install python3-pip git

RUN pip3 install flask-restful requests gunicorn python-bitcoinlib pika

LABEL version="20181127a"
RUN git clone https://github.com/Utrum/hodl-api.git \
  && cd hodl-api \
  && git checkout dev

CMD cd hodl-api \
  && gunicorn --access-logfile - -b 0.0.0.0:5000 -w 8 hodl_server:app
 
