from time import sleep
import time
import datetime


#from networkx import gaussian_random_partition_graph
import RPi.GPIO as gpio
import math
import csv
import datetime

csv_file ="45deg_movement.txt"

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

Green_led_dynamic = 23
Green_led_static = 24


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

gpio.setup(Green_led_dynamic, gpio.OUT)
gpio.setup(Green_led_static, gpio.OUT)

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

Calibration_File_Name_start = "CalFile"
Calibration_File_Name_suffix = "cal"
CurrentCalibration_File_Name =  "CurrentCalib.cal"

def CreateTimeStamp(x: time):
    result = str(x)
    return result

def Led_Squencer(blink, dwell, gap):
    led_time_states: led_time_state = []
    led1 = Green_led_static # saccad rod led
    led2 = Green_led_dynamic # dynamic led
    seq_time = 13.0 #total saccad time
    time_slice = 0.1 #time increments where all changes occur.
    steps = math.ceil(seq_time/time_slice)+1
    # fill the led_times_states list here
     
    # algorithm for fixation and gap time, gap time is negative for an overlap and positive for a gap 
    # blink offsets the start time    
    # fixation from Saccade_Instruction class: dwell
    # gap from Saccade_Instruction class: gap   
    sequence = []
    sequence.append( int(blink/4 * 0 / time_slice))                    #led1 on 0
    sequence.append( int(blink/4 * 1 / time_slice ))                    #led1 off 2
    sequence.append( int(blink/4 * 2 / time_slice))                    #led1 on 4
    sequence.append( int(blink/4 * 3 / time_slice))                    #led1 off 6
    sequence.append( int(blink / time_slice))                          #led1 on 8
    sequence.append(int((dwell + gap + blink) / time_slice ))         #led2 on 46
    sequence.append( int(((dwell + blink) / time_slice)))                #led1 off 48
    sequence.append(int((2*dwell + 2*gap + blink) / time_slice))      #led1 on 84
    sequence.append(int((2*dwell + gap + blink) / time_slice))        #led2 off 86
    sequence.append(int((3*dwell + 2*gap + blink) / time_slice))      #led1 off 124
    
    print(sequence)
    for t in range(steps): # time increments is t
        if t == sequence[0] or t == sequence[2] or t == sequence[4] or t == sequence[7]:
            gpio.output(led1,gpio.HIGH)
            print(f"led1 on step {t}")
        elif t == sequence[1] or t == sequence[3] or t == sequence[6] or t == sequence[9]:
            gpio.output(led1,gpio.LOW)
            tstamp = time.time()
            ts_string = CreateTimeStamp(tstamp)
            print(f"led1 off step {t} {ts_string}")
        elif t == sequence[5]:
            gpio.output(led2,gpio.HIGH)
            print(f"led2 on step {t}")
        elif t == sequence[8]:
            gpio.output(led2,gpio.LOW)
            tstamp = time.time()
            ts_string = CreateTimeStamp(tstamp)
            print(f"led2 off step {t} {ts_string}")
        sleep(0.1)
    return 0

gpio.output(Green_led_static,0)
gpio.output(Green_led_dynamic,0)
sleep(1)
gpio.output(Green_led_static,1)
gpio.output(Green_led_dynamic,1)
sleep(1)
gpio.output(Green_led_static,0)
gpio.output(Green_led_dynamic,0)
sleep(1)
gpio.output(Green_led_static,1)
gpio.output(Green_led_dynamic,1)
sleep(1)
gpio.output(Green_led_static,0)
gpio.output(Green_led_dynamic,0)
sleep(1)

Led_Squencer(0.8,4,-0.2)

print("end sequence")
gpio.output(Green_led_static,0)
gpio.output(Green_led_dynamic,0)