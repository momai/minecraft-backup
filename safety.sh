#!/bin/bash

# Get the percentage of used space on /dev/md2
used_percentage=$(df -h /dev/md2 | awk 'NR==2{print $5}' | tr -d '%')

# Check if the used percentage is greater than 90%
if [ "$used_percentage" -gt 90 ]; then
    echo "Stopping service due to low disk space." >> /var/log/service_stop_reason.log
    # Replace 'your_service_name' with the actual name of the service you want to stop
    systemctl stop original-server
    systemctl disable original-server
else
    echo "Sufficient space available. No action required."
fi
