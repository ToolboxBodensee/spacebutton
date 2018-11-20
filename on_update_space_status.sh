if [ "x$1" = "xopen" ]; then
#hdmi on
tvservice -p
systemctl start info-beamer.service
else
systemctl stop info-beamer.service
#hdmi signal off
tvservice -o
fi
