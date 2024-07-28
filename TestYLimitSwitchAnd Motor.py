from time import sleep
import RPi.GPIO as gpio
import math
import csv

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
gpio.output(direction_pinY,cw_direction) # y axis motor

cycle=True
x_step_count=0
z_step_count=0
y_step_count=0

x_max = -1
z_max = -1
y_max = -1

move_out_steps_max_X = 20
move_out_steps_max_Z = 20
move_out_steps_max_Y = 20


for y in range(20):
    gpio.output(direction_pinY,cw_direction)
    print("y motor test move CW") #moves down
    for x in range(200):
        if gpio.input(y_axis_limit)==0:
            gpio.output(pulse_pinY,gpio.HIGH)
            sleep(.001)
            gpio.output(pulse_pinY,gpio.LOW)
            sleep(.0005)
        
    sleep(1)
    gpio.output(direction_pinY,ccw_direction)
    print("y motor test move ccw") # moves up

    for x in range(200):
        if gpio.input(y_axis_limit)==0:
            gpio.output(pulse_pinY,gpio.HIGH)
            sleep(.001)
            gpio.output(pulse_pinY,gpio.LOW)
            sleep(.0005)
    
     
print("Motor test complete")
        

    