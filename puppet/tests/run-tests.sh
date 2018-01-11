#!/bin/bash

sitepack=$(python -c 'import sys; \
           sitedirs=[p for p in sys.path if p.endswith("site-packages")]; \
           print sitedirs[0]')

declare -a files

for f in [a-z]*.py
do
    link=${f//-/_} 
    if [[ ! -L $link ]]
    then
        ln -s $f $link
        files[${#files[@]}]="$link"
    fi
done

if [[ ! -e __init__.py ]]
then 
    touch __init__.py
    files[${#files[@]}]="__init__.py"
fi

coverage run --source=tests -m unittest2 discover tests -v && coverage xml

for f in ${files[@]}
do
    rm -f $f*
done
