from time import sleep
import RPi.GPIO as gpio

direction_pin   = 21
pulse_pin       = 20
direction_pin2  = 19
pulse_pin2      = 26
#direction_pin3  = 13
#pulse_pin3      = 6

cw_direction    = 0 
ccw_direction   = 1 
x_axis_limit    = 17
z_axis_limit    = 27
gpio.setmode(gpio.BCM)
gpio.setup(direction_pin, gpio.OUT)
gpio.setup(direction_pin2, gpio.OUT)

gpio.setup(pulse_pin, gpio.OUT)
gpio.setup(pulse_pin2, gpio.OUT)
gpio.setup(x_axis_limit, gpio.IN)
gpio.setup(z_axis_limit, gpio.IN)

gpio.output(direction_pin,cw_direction) # left motor (A)
gpio.output(direction_pin2,ccw_direction) # right motor (b)



try:
    while True:
        print("Cycle Starting")
        sleep(2)
        print('Direction CW LeftMotor')
        #gpio.output(direction_pin,cw_direction)
        gpio.output(direction_pin2,ccw_direction)
        for x in range(400):
            if(gpio.input(z_axis_limit)==0 and gpio.input(x_axis_limit)==0):
                #gpio.output(pulse_pin,gpio.HIGH)
                gpio.output(pulse_pin2,gpio.HIGH)
                sleep(.001)
                #gpio.output(pulse_pin,gpio.LOW)
                gpio.output(pulse_pin2,gpio.LOW)         
                sleep(.0005)

        sleep(2)
        print('Direction CCW Left Motor')
        #gpio.output(direction_pin,ccw_direction)
        gpio.output(direction_pin2,cw_direction)
        
        for x in range(400):
            if(gpio.input(z_axis_limit)==0 and gpio.input(x_axis_limit)==0):
                #gpio.output(pulse_pin,gpio.HIGH)
                gpio.output(pulse_pin2,gpio.HIGH)
                sleep(.001)
                #gpio.output(pulse_pin,gpio.LOW)
                gpio.output(pulse_pin2,gpio.LOW)
                sleep(.0005)

except KeyboardInterrupt:
    gpio.cleanup()
