# 🐣 Vögeli is a Raspberry Pi based birdhouse monitor

Vögeli features a livestream with the PiCamera2 including infrared light source to enhance vision at night. A Sensirion
SHT40 is used to monitor humidity and temperature inside the birdhouse. A custom mail script is used to inform
subscribers if any movement is detected inside the birdhouse.

A custom email implementation (`unibe_mail`, closed-source) is required for the email-alerts.