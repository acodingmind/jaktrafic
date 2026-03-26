#!/bin/sh

DIR="jup"

echo
echo "*** rendering all notebooks"
if [ -d "$DIR" ]; then
  echo "${DIR} found"
  jupyter nbconvert --to html --output-dir='app/html/local/notes' --no-prompt --no-input jup/*.ipynb
else
  echo "${DIR} does not exist"
fi

echo
echo "*** rendering ready"
echo