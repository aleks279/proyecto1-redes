from gpiozero import Buzzer

#Set on pin 17
bz = Buzzer(17)



f = open("myfile", "rb")

try:
    byte = f.read(1)
    while byte != "":
        # Do stuff with byte.
        byte = f.read(1)

        bz.on()
finally:
    f.close()
