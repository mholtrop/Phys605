#!/bin/bash
# Simple script to help getting you onto the UNH secure network.
# Run as: "sudo UNH_Secure_setup.sh"
#
# Written by Prof. Maurik Holtrop, Feb 2021
#
# This is for Raspian Buster.
#
fix_the_wpa_supplicant_bug(){
    # Backup the faulty 10-wpa-supplicant file.
    echo "If promted, supply the password for your user account on this system."
    sudo cp /lib/dhcpcd/dhcpcd-hooks/10-wpa_supplicant .
    sudo chown ${USER} 10-wpa_supplicant 
    # edit and put replacement back.
    sed 's/nl80211,wext/wext,nl80211/' 10-wpa_supplicant > 10-wpa_supplicant_new
    sudo cp -f 10-wpa_supplicant_new /lib/dhcpcd/dhcpcd-hooks/10-wpa_supplicant
}

get_certificates(){
    # Passwordless certificates stored on GitHub
    
}

get_info() {
    echo "Please enter your UNH username (without any @wildcat or @cisunix)"
    echo "and also enter the corresponding password. The same you used to"
    echo "log in on the webpage before."

    read -p "UNH Username: " user
    echo
    while true; do
	read -s -p "UNH Password (the text will not show up): " passw
	echo
	read -s -p "Type your password again to verify: " passwTest
	echo
	
	if [ $passw != $passwTest ]; then
	    echo "Passwords do not match, try again..."
	    echo
	else
	    break
	fi
    done
}

change_passw_certs(){
    if [ -r ${user}@cpuserunhedu.cer ]; then
	cp ${user}@cpuserunhedu.cer cpuserunhedu.cer
    else 
	echo "ERROR - Could not find the certificate. Did you use the correct username?"
	exit
    fi
    if [ -r ${user}@cpuserunhedu.key ]; then
	openssl rsa -des3 -in ${user}@cpuserunhedu.key -out cpuserunhedu.key -passin pass:${passw} -pasout pass:fizzix=phun
    else
	echo "ERROR - Could not find the certificate. Did you use the correct username?"
	exit
    fi

    sudo cp cpuserunhedu.* /etc/ssl/certs
    sudo cp CA-*.cer /etc/ssl/certs
}

main() {
	intro
	echo "======================================"
	echo "This script will attempt to automatically setup wifi connection to UNH Secure"
	echo "on your Raspberry Pi. "
	echo "You will need your UNH username and password"
	echo "(same as you use for logging into Canvas)"
	echo "You will *also* need the password for the 'pi' account in this system."
	cd ~/Downloads 
	echo "UNH Wifi setup started " >> UNH_Wifi.log
	date >> UNH_Wifi.log
	guide_to_get_certificates
	fix_the_wpa_supplicant_bug
	get_info
	change_passw_certs
	

	popd
	echo
	echo "IMPORTANT: Restart your system, then try to connect to UNH-Secure via the wifi menu. Good luck."
}

main

exit 0
