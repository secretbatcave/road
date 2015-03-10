#!/usr/bin/perl


`killall gpsd`;
`stty speed 57600 < /dev/ttyUSB0 && gpsd -n /dev/ttyUSB0 `;
