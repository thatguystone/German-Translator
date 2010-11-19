#!/bin/zsh
#Builds the MySQLdb module on the webserver
#This should be run from /cgi-bin

echo "Content-type: text/html\n\n"
echo "<pre>"

cd /home/abs407/deutsch/libraries/MySQL-python-1.2.3

#ls /usr/sfw/lib

#1) run this
#python setup.py build

#2) comment out `python setup.py build`
#3) run the following 3 lines 
gcc -I/home/abs407/deutsch/libraries/mysql-5.1.52/include -I/usr/include/python2.4 -c _mysql.c -o build/temp.solaris-2.10-sun4u-2.4/_mysql.o
export LD_RUN_PATH=/home/abs407/deutsch/libraries/mysql-5.1.52/libmysql/.libs
gcc -G build/temp.solaris-2.10-sun4u-2.4/_mysql.o -L/home/abs407/deutsch/libraries/mysql-5.1.52/libmysql/.libs -lmysqlclient -lz -lposix4 -lgen -lsocket -lnsl -lm -o build/lib.solaris-2.10-sun4u-2.4/_mysql.so 

