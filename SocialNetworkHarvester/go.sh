#!/bin/bash
gedit $(find -type f | grep "py$" | grep -v __init__) $(find -type f | grep "html$") $(find -type f | grep "css$")  &> /dev/null &
