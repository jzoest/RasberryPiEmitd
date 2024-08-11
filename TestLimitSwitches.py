from time import sleep
import RPi.GPIO as gpio

direction_pin   = 21
pulse_pin       = 20
direction_pin2  = 19
pulse_pin2      = 26
direction_pinY  = 13
pulse_pinY      = 6

cw_direction    = 0 
ccw_direction   = 1 
x_axis_limit    = 17
z_axis_limit    = 27
y_axis_limit    = 22

gpio.setmode(gpio.BCM)
gpio.setwarnings(False)

gpio.setup(direction_pin, gpio.OUT)
gpio.setup(direction_pin2, gpio.OUT)
gpio.setup(direction_pinY, gpio.OUT)

gpio.setup(pulse_pin, gpio.OUT)
gpio.setup(pulse_pin2, gpio.OUT)
gpio.setup(pulse_pinY, gpio.OUT)

gpio.setup(x_axis_limit, gpio.IN)
gpio.setup(z_axis_limit, gpio.IN)
gpio.setup(y_axis_limit, gpio.IN)


gpio.output(direction_pin,cw_direction) # left motor (A)
gpio.output(direction_pin2,ccw_direction) # right motor (b)

cycle = True

try:
    while cycle== True:
        print("Press X limit switch right")
        while( gpio.input(x_axis_limit) == 0):
            sleep(0.5)
        sleep(2)
        print("Press X limit switch left")
        while( gpio.input(x_axis_limit) == 0):
            sleep(0.5)
        sleep(2)
        print("Press Z limit switch back")
        while( gpio.input(z_axis_limit) == 0):
            sleep(0.5)
        sleep(2)
        print("Press Z limit switch front")
        while( gpio.input(z_axis_limit) == 0):
            sleep(0.5)
        sleep(2)
        print("Press Y limit switch top")
        while( gpio.input(y_axis_limit) == 0):
            sleep(0.5)
        sleep(2)
        print("Press Y limit switch bottom")
        while( gpio.input(y_axis_limit) == 0):
            sleep(0.5)
        sleep(2)
        print("Limit switch testing complete")
        
        print("Cycle Starting Z Axis (aka y)")
        sleep(5)
        print('Direction CW Left CCW Right')
        gpio.output(direction_pin,cw_direction)
        gpio.output(direction_pin2,ccw_direction)
        for x in range(400):
            if(gpio.input(z_axis_limit)==0 and gpio.input(x_axis_limit)==0):
                gpio.output(pulse_pin,gpio.HIGH)
                gpio.output(pulse_pin2,gpio.HIGH)
                sleep(.001)
                gpio.output(pulse_pin,gpio.LOW)
                gpio.output(pulse_pin2,gpio.LOW)         
                sleep(.0005)

        sleep(5)
        print('Direction CCW left CW Right')
        gpio.output(direction_pin,ccw_direction)
        gpio.output(direction_pin2,cw_direction)
        
        for x in range(400):
            if(gpio.input(z_axis_limit)==0 and gpio.input(x_axis_limit)==0):
                gpio.output(pulse_pin,gpio.HIGH)
                gpio.output(pulse_pin2,gpio.HIGH)
                sleep(.001)
                gpio.output(pulse_pin,gpio.LOW)
                gpio.output(pulse_pin2,gpio.LOW)
                sleep(.0005)
        cycle = False
except KeyboardInterrupt:
    gpio.cleanup()
