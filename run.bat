#!/bin/sh

@echo off

git pull && git submodule foreach --recursive "(git remote -v ; git pull; echo; echo ...)"

python start.py
