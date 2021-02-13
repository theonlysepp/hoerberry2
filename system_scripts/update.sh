#!/bin/bash
# aufrufen mit  "bash update.sh"
# derzeit nur als Vorlage fuer die Kommandozeileneingabe verwendbar. 
echo "Koepieren der aktuellen autostart.service file zur richtigen Stelle"
sudo cp $HOME/hoerberry2/system_scripts/autostart.service /etc/systemd/system/autostart.service
sudo cp $HOME/hoerberry2/system_scripts/autostart_test.service /etc/systemd/system/autostart_test.service

sudo cp $HOME/hoerberry2/settings_and_data/base_settings.ini /boot/base_settings.ini