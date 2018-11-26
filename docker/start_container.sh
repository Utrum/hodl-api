#!/bin/bash
( cd ../ && docker run \
  --rm -d \
  --name=hodl_api \
  --net=host \
  -v=`pwd`/conf:/hodl-api/conf \
  kmdplatform/hodl-api )

