from gpiozero import Buzzer

#Set on pin 17
bz = Buzzer(17)
from gpiozero import Buzzer
from time import sleep

def buzzerOnOne():

        i = 0
        bz = Buzzer(17)

        while  i < 1 :

                bz.on()
                sleep(1)
                bz.off()
		sleep(1.4)
                i = i + 1
                print ( "Sound" )


f = open("allan.txt", "rb")
byte = "C"
try:

    while byte != "":
        # Do stuff with byte.
        byte =  f.read(1)
	if len(byte) != 0 :
           binar = bin(ord(byte))
	   print(binar)
           lenBin = len(binar)
           print(lenBin)
           cont = 0
           while cont != lenBin:
               element = binar[cont]
               if element == '1':
                  buzzerOnOne()
                  print(element)
               else:
                  print(element)
               cont = cont + 1 

finally:
    f.close()






f = open("myfile", "rb")

try:
    byte = f.read(1)
    while byte != "":
        # Do stuff with byte.
        byte = f.read(1)

        bz.on()
finally:
    f.close()
