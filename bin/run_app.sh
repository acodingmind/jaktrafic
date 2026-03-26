#!/bin/sh

DIR="venv"
export FLASK_ENV='lite'
source ${DIR}/bin/activate

python3 -m flask run --host=0.0.0.0
