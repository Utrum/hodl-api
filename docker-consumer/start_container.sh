#!/bin/bash
( cd ../ && docker run \
  --rm -d \
  --name=hodl_consumer \
  --net=host \
  -v=`pwd`/conf:/hodl-api/conf \
  -e PYTHONUNBUFFERED=0 \
  kmdplatform/hodl-api:consumer )

