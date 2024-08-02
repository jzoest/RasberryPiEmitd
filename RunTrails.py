from time import sleep
import time

import RPi.GPIO as gpio
import math
import csv
import datetime

import os

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
Input_File_Path = ".//input_files"

class target_position:
    X = 0
    Y = 0
    Z = 0
    
    def __init__ ( self, x,y,z):
        self.X = x
        self.Y = y
        self.Z = z
        
    def vector_distanceXZ(self, other_position):
        if other_position is not None:
            return math.hypot(other_position.X-X, other_position.Z-Z)
        else:
            return -1
        
    def vector_angleXZ_deg(self, other_position):
        if other_position is not None:
            return math.degrees(math.atan(other_position.Z-Z/other_position.X-X))
        else:
            return -999

    def vector_angleXZ_rad(self, other_position):
        if other_position is not None:
            return math.atan(other_position.Z-Z/other_position.X-X)
        else:
            return -999
 
class Led_time_state:
    led_number:int = 0 # led 1 = static, led 2 = dynamic
    led_state:int = 0   # off = 0 on = 1
    timeSliceNumber:int = 0 # number of steps for start of sequence
    
    def __init__ (self,led_no,state,sliceNumber):
        self.led_number = led_number
        self.led_state = state
        self.timeSliceNumber = sliceNumber
        
        

def move_to_position(new_position, current_position, step_time):
    delta_x = new_position.X - current_position.X
    delta_y = new_position.Y - current_position.Y
    delta_z = new_position.Z - current_position.Z
    
    delta_M_A = delta_x - delta_z 
    delta_M_B = delta_x + delta_z 
    
    if abs(delta_M_A) > abs(delta_M_B):
        max_steps= abs(delta_M_A)
    else:
        max_steps= abs(delta_M_B)
        
    a_steps=abs(delta_M_A)
    b_steps=abs(delta_M_B)
    
    # set direction
    if delta_M_A < 0:
        gpio.output(direction_pin,cw_direction)
        #gpio.output(direction_pin,ccw_direction)
    else:
        gpio.output(direction_pin,ccw_direction)
        #gpio.output(direction_pin,ccw_direction)
        
    if delta_M_B < 0:
        gpio.output(direction_pin2,cw_direction)
    else:
        gpio.output(direction_pin2,ccw_direction)
    
    for x in range(max_steps):
        if(gpio.input(x_axis_limit) == 0 and gpio.input(z_axis_limit) == 0):
            if x < a_steps:
                gpio.output(pulse_pin,gpio.HIGH)
            if x < b_steps:
                gpio.output(pulse_pin2,gpio.HIGH)
            sleep(step_time)
            if x < a_steps:
                gpio.output(pulse_pin,gpio.LOW)
            if x < b_steps:
                gpio.output(pulse_pin2,gpio.LOW)
            sleep(step_time/2)
    # workout Y direction
    if delta_y<0:
        gpio.output(direction_pinY,cw_direction)
    else:
        gpio.output(direction_pinY,ccw_direction)
    # now do Y steps/movement
    for x in range(abs(delta_y)):
        if gpio.input(y_axis_limit) == 0:
            gpio. output(pulse_pinY, gpio.HIGH)
            sleep(step_time)
            gpio.output(pulse_pinY, gpio.LOW)
            sleep(step_time/2)
        
            
def CreateFileName(x: datetime):
    year  = x.year
    month = x.month
    day   = x.day
    hr    = x.hour
    mins  = x.minute
    sec   = x.second
    result = f"{Calibration_File_Name_start}{year}{month}{day}T{hr}{mins}{sec}.{Calibration_File_Name_suffix}"
    return result

def CreateLogFileName(x: datetime):
    year  = x.year
    month = x.month
    day   = x.day
    hr    = x.hour
    mins  = x.minute
    sec   = x.second
    result = f"Run_Trials_Log_{year}{month}{day}T{hr}{mins}{sec}.log"
    return result
    
def Led_Squencer(blink, dwell, gap):
    led_time_states: led_time_state = []
    led1 = Green_led_static # saccad rod led
    led2 = Green_led_dynamic # dynamic led
    seq_time = 12.5 #total saccad time
    time_slice = 0.1 #time increments where all changes occur.
    steps = math.ceil(seq_time/time_slice)
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
            ts_string = str(tstamp)
            print(f"led1 off step {t} {ts_string}")
        elif t == sequence[5]:
            gpio.output(led2,gpio.HIGH)
            print(f"led2 on step {t}")
        elif t == sequence[8]:
            gpio.output(led2,gpio.LOW)
            tstamp = time.time()
            ts_string = str(tstamp)
            print(f"led2 off step {t} {ts_string}")
        sleep(0.1)
    return 0

try:
    logstart = datetime.datetime.now()
    logFileName = CreateLogFileName(logstart)
    log = open(logFileName,"w")
    print(f"Running Trials at {logstart}")
    while cycle== True:
        log.write("Home Axis\n")
        log.write('X axis move to start posn\n')
        gpio.output(direction_pin,cw_direction)
        gpio.output(direction_pin2,cw_direction)
        
        if(gpio.input(x_axis_limit)!=0):
            for x in range(move_out_steps_max_X):
                gpio.output(pulse_pin2,gpio.HIGH)
                gpio.output(pulse_pin,gpio.HIGH)
                sleep(.001)
                gpio.output(pulse_pin2,gpio.LOW)
                gpio.output(pulse_pin,gpio.LOW)
                sleep(.0005)
            sleep(1)
            
        gpio.output(Green_led_dynamic,gpio.HIGH) # Green led on
        
        while(gpio.input(x_axis_limit) == 0):
            gpio.output(pulse_pin2,gpio.HIGH)
            gpio.output(pulse_pin,gpio.HIGH)
            sleep(.001)
            gpio.output(pulse_pin2,gpio.LOW)
            gpio.output(pulse_pin,gpio.LOW)         
            sleep(.0005)
        log.write('X axis is at X Home position\n')
        gpio.output(Green_led_dynamic,gpio.LOW) # Green led off
        sleep(1)
        gpio.output(direction_pin2,ccw_direction)
        gpio.output(direction_pin,ccw_direction)
        
        # move away from start
        if(gpio.input(x_axis_limit)!=0):
            for x in range(move_out_steps_max_X):
                gpio.output(pulse_pin2,gpio.HIGH)
                gpio.output(pulse_pin,gpio.HIGH)
                sleep(.001)
                gpio.output(pulse_pin2,gpio.LOW)
                gpio.output(pulse_pin,gpio.LOW)
                sleep(.0005)
            sleep(1)
            
        
        log.write("Z axis home cycle\n")
        gpio.output(direction_pin,ccw_direction) # to motors
        gpio.output(direction_pin2,cw_direction)
        
        if(gpio.input(z_axis_limit)!=0):
            for x in range(move_out_steps_max_Z):
                gpio.output(pulse_pin,gpio.HIGH)
                gpio.output(pulse_pin2,gpio.HIGH)
                sleep(.001)
                gpio.output(pulse_pin,gpio.LOW)
                gpio.output(pulse_pin2,gpio.LOW)
                sleep(.0005)
            sleep(1)
        
        gpio.output(Green_led_dynamic,gpio.HIGH) # Green led on
        log.write("Move to Z axis home\n")
        while(gpio.input(z_axis_limit)==0):
            gpio.output(pulse_pin,gpio.HIGH)
            gpio.output(pulse_pin2,gpio.HIGH)
            sleep(.001)
            gpio.output(pulse_pin,gpio.LOW)
            gpio.output(pulse_pin2,gpio.LOW)
            sleep(.0005)
        
        log.write('Z axis in home position\n')
        sleep(1)
        gpio.output(Green_led_dynamic,gpio.LOW) # Green led off
        
        gpio.output(direction_pin,cw_direction) # away from motors
        gpio.output(direction_pin2,ccw_direction)
        
        if(gpio.input(z_axis_limit)!=0):
            for x in range(move_out_steps_max_Z):
                gpio.output(pulse_pin,gpio.HIGH)
                gpio.output(pulse_pin2,gpio.HIGH)
                sleep(.001)
                gpio.output(pulse_pin,gpio.LOW)
                gpio.output(pulse_pin2,gpio.LOW)
                sleep(.0005)
            sleep(1)
                        
        log.write("Y axis calibration move to home position\n")
        
        gpio.output(direction_pinY,cw_direction)
        if(gpio.input(y_axis_limit)!=0):
            for x in range(move_out_steps_max_Y):
                gpio.output(pulse_pinY,gpio.HIGH)
                sleep(0.001)
                gpio.output(pulse_pinY,gpio.LOW)
                sleep(0.0005)
            sleep(1)
            
        gpio.output(direction_pinY,cw_direction)    
        while(gpio.input(y_axis_limit)==0):
            gpio.output(pulse_pinY,gpio.HIGH)
            sleep(0.001)
            gpio.output(pulse_pinY,gpio.LOW)
            sleep(0.0005)
        sleep(1)
        
        gpio.output(direction_pinY,ccw_direction)
        if(gpio.input(y_axis_limit)!=0):
            for x in range(move_out_steps_max_Y):
                gpio.output(pulse_pinY,gpio.HIGH)
                sleep(0.001)
                gpio.output(pulse_pinY,gpio.LOW)
                sleep(0.0005)
            sleep(1)
        log.write("Y axis is at Home position\n")
        log.flush()
        log.write("Reading Calibration file {CurrentCalibration_File_Name}\n")
        with open(CurrentCalibration_File_Name) as Calfile:
            calreader = csv.reader(Calfile)
            row_count = 0
            for row in calreader:
                if row_count == 0:
                    row_count+=1
                    continue
                elif row_count == 1:
                    CalDate = row[0]
                    x_max = int(row[1])
                    y_max = int(row[2])
                    z_max = int(row[3])
                    row_count+=1
                else:
                    row_count+=1
                    continue
                
        
        log.write(f"Read Calibration file Created {CalDate} X Max = {x_max} Y Max = {y_max} Z Max = {z_max}\n")
        log.flush()
        if x_max > 900 and z_max > 1900 and y_max > 1200:
            log.write("Calibration appears to be good\n")
        else:
            log.write("calibration is invalid one or more axis are not calibrated correctly\n")
            log.write("Please re-calibrate\n")
            print("calibration is invalid one or more axis are not calibrated correctly")
            print("Please re-calibrate")
            log.close()
            exit(-1)
        for b in range(4):
            gpio.output(Green_led_dynamic,gpio.HIGH) # Green led on
            sleep(0.25)
            gpio.output(Green_led_dynamic,gpio.LOW) # Green led off
            sleep(0.25)
         
        log.write("At Home now ready and calibrated\n")
        current = target_position(0,0,0)
        newposition = target_position(math.floor(x_max/2),0,0)
        start = time.time()
        move_to_position(newposition,current,0.001)
        end = time.time()
        log.write(f"x move time {end - start}\n")
        current = newposition
        log.write(f" Postion is X = {current.X} Y= {current.Y} = {current.Z}\n")
        start = time.time()
        nextposition=target_position(math.floor(x_max/2),0,math.floor(z_max*0.5))
        move_to_position(nextposition,current,0.001)
        end = time.time()
        log.write(f"z move time {end - start}\n")
        current = nextposition
        log.write(f" Postion is X = {current.X} Y= {current.Y} = {current.Z}\n")
        nextposition=target_position(math.floor(x_max/2),math.floor(y_max*0.5),math.floor(z_max*0.5))
        move_to_position(nextposition,current,0.001)
        current = nextposition
        log.write(f" Postion is X = {current.X} Y= {current.Y} = {current.Z}\n")
        log.flush()
        os.fsync(log)
        my_file_list = []
        for file in os.listdir(Input_File_Path):
            if file.endswith(".csv"):
               my_file_list.append(file)
               log.write(f"Adding file {file} to list of files for trial\n")
               
        log.flush()
        os.fsync(log)
        
        
        for file in my_file_list:
            print(file)
            with open(csv_file) as file:
                heading = next(file)
                reader = csv.reader(file)
                for row in reader:
                    print(current.X, current.Z)
                    if row[0]!="end":
                        x_position = math.floor(float(row[4])*x_max) # wrong way for 0.4 -- went left, should have been right
                        z_position = math.floor(float(row[5])*z_max) # correct way for 0.6 -- went back
                        log.write(f" Postion is X = {current.X} Y= {current.Y} = {current.Z}\n")
                        wait_time = int(row[7])/1000
                        nextposition2 = target_position(x_position,0,z_position)
                        move_to_position(current,nextposition2,0.001)
                        current=nextposition2
                        # To do add led sequence stuff
                        sleep(wait_time)
                
        print("Done csv commands")
        log.close()
        for b in range(10):
            gpio.output(Green_led,gpio.HIGH) # Green led on
            sleep(0.5)
            gpio.output(Green_led,gpio.LOW) # Green led off
            sleep(0.5)
            
        cycle=False
        print(" cycle end")
        exit()
        
except KeyboardInterrupt:
    gpio.cleanup()
