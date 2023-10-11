#!/bin/bash

# read cfg file:
if [ -f "cfg" ]; then
    source cfg
fi

if [ -d "src/lac/" ]; then
    cd src/lac/
fi

cd unix/unix_scripts
sudo python3 service.py
