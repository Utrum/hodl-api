#!/bin/bash
( cd ../ && docker run --rm -ti --net=host -v=`pwd`/conf:/hodl-api/conf kmdplatform/hodl-api )

