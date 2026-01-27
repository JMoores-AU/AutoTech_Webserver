#!/bin/bash
echo -n "Please Enter MySQL User Name :"
read mysql_un
echo -n "Please Enter MySQL Password  :"
read -s mysql_pw
echo ""

#echo "**** Current Database Size ****"
echo -e '\e[31m **** Current Database Size **** \e[m'
echo -ne "Location Survey\t: "
mysql -N -s -e "select count(*) from survey_location__shapeloc__x_y_z;" -u $mysql_un --password=$mysql_pw frontrunnerV3 2>/dev/null
echo -ne "Road Survey\t: "
mysql -N -s -e "select count(*) from survey_path__shapepath__x_y_z;" -u $mysql_un --password=$mysql_pw frontrunnerV3 2>/dev/null
echo -ne "Course\t\t: "
mysql -N -s -e "select count(*) from course__coursegeometry__x_y_z;" -u $mysql_un --password=$mysql_pw frontrunnerV3 2>/dev/null
echo -ne "Dump Node\t: "
mysql -N -s -e "select count(*) from dump_node;" -u $mysql_un --password=$mysql_pw frontrunnerV3 2>/dev/null

