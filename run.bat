#!/bin/sh

@echo off

git pull && git submodule foreach --recursive "(git remote -v ; git checkout master; git pull; echo ^^^; echo ...)"

#for X in $(cat .gitmodules | grep path.= | sed 's/.*= //'); do Y=$(pwd); gtouch $X ; echo ^__ ; cd $Y; done

python start.py
