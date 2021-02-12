#!/bin/bash
# Simple script to help getting you onto the UNH secure network.
# Run as: "./UNH_Secure_setup.sh"
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
    wget -q https://raw.githubusercontent.com/mholtrop/Phys605/master/UNH_Wifi/mholtrop.cer
    wget -q https://raw.githubusercontent.com/mholtrop/Phys605/master/UNH_Wifi/private.key
    wget -q https://raw.githubusercontent.com/mholtrop/Phys605/master/UNH_Wifi/CA-27AC9369FAF25207BB2627CEFACCBE4EF9C319B8.cer
    wget -q https://raw.githubusercontent.com/mholtrop/Phys605/master/UNH_Wifi/CA-47BEABC922EAE80E78783462A79F45C254FDE68B.cer
    sudo cp mholtrop.cer private.key CA-27AC9369FAF25207BB2627CEFACCBE4EF9C319B8.cer CA-47BEABC922EAE80E78783462A79F45C254FDE68B.cer /etc/ssl/certs/
}

replace_wpa_supplicant_conf(){
    # Add the proper entry to the wpa_supplicant.conf file.
    cp /etc/wpa_supplicant/wpa_supplicant.conf ~/Downloads/wpa_supplicant.conf_orig
    wget -q https://raw.githubusercontent.com/mholtrop/Phys605/master/UNH_Wifi/wpa_supplicant.conf
    sudo cp wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf 
}

get_new_networkname(){
    # Ask for the number on the RPi.
    read -p "Please enter the number on your RPi: "  pi_num
    newname=phys605pi${pi_num}
    sudo hostname ${newname}
    sudo echo ${newname} > new_hostname
    sudo cp new_hostname /etc/hostname
}

restart_network(){
    # Restart the wireless network
    sudo killall wpa_supplicant
    sudo systemctl restart dhcpcd
    read -p "Please type type <enter> key to continue"
}

main() {
	echo "=============================================================================="
	echo "This script will attempt to automatically setup wifi connection to UNH Secure"
	echo "on your Raspberry Pi. "
	echo "You will need the password for the 'pi' account in this system."
	echo "(or the password for the account you logged in with.)"
	echo "You can ignore the 'sudo: unable to resolve ...' mesages."
	echo "=============================================================================="
	cd ~/Downloads 
	echo "UNH Wifi setup started " >> UNH_Wifi.log
	date >> UNH_Wifi.log
	get_certificates
	fix_the_wpa_supplicant_bug
	replace_wpa_supplicant_conf
	get_new_networkname
	restart_network
	echo
	echo "Your system should get networking now. "
	echo "Your network address will be ${newname}.aw4.unh.edu "
}

main

exit 0
