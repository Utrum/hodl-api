FROM ubuntu:16.04

RUN apt update && apt -y install python3-pip git

RUN pip3 install flask-restful requests gunicorn python-bitcoinlib

LABEL version="20181126b"
RUN git clone https://github.com/Utrum/hodl-api.git \
  && cd hodl-api \
  && git checkout dev

CMD cd hodl-api \
  && ./consumer.py
 
