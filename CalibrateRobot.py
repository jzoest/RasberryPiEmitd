from time import sleep
import time

import RPi.GPIO as gpio
import math
import csv
import datetime

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
    result = f"Calibration_Log_{year}{month}{day}T{hr}{mins}{sec}.log"
    return result


try:
    logstart = datetime.datetime.now()
    logFileName = CreateLogFileName(logstart)
    log = open(logFileName,"w")
    print(f"Starting Calibration at {logstart}")
    confirm = False
    while not confirm:
        response = input("Please confirm Saccada Rod is removed from the Robot (Y/N)")
        log.write(f"Comfirmed Saccada Rod Removed {response}\n")
        if(response.startswith("y") or response.startswith("Y")):
            confirm = True
        else:
           print("Invalid response please enter (Y/N) after removing the saccada rod from the Robot")
           log.write("Invalid response recieved ask again\n")
    
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
            
        gpio.output(Green_led_static,gpio.HIGH) # Green led on
        
        while(gpio.input(x_axis_limit) == 0):
            gpio.output(pulse_pin2,gpio.HIGH)
            gpio.output(pulse_pin,gpio.HIGH)
            sleep(.001)
            gpio.output(pulse_pin2,gpio.LOW)
            gpio.output(pulse_pin,gpio.LOW)         
            sleep(.0005)
        log.write('X axis is at X Home position\n')
        gpio.output(Green_led_static,gpio.LOW) # Green led off
        sleep(1)
        log.write('X axis move to end posn to determine max steps\n')
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
            
        gpio.output(Green_led_static,gpio.HIGH) # Green led on    
        while(gpio.input(x_axis_limit) == 0):
            gpio.output(pulse_pin2,gpio.HIGH)
            gpio.output(pulse_pin,gpio.HIGH)
            sleep(.001)
            gpio.output(pulse_pin2,gpio.LOW)
            gpio.output(pulse_pin,gpio.LOW)
            sleep(.0005)
            x_step_count+=1
            
        log.write(f"Steps in X axis is {x_step_count}\n")
        x_max=x_step_count
        gpio.output(Green_led_static,gpio.LOW) # Green led off
        sleep(1)
        
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
        
        gpio.output(Green_led_static,gpio.HIGH) # Green led on
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
        gpio.output(Green_led_static,gpio.LOW) # Green led off
        
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
            
        log.write("Move to Z axis end to count number of steps\n")
        gpio.output(Green_led_static,gpio.HIGH) # Green led on
        while(gpio.input(z_axis_limit)==0):
            gpio.output(pulse_pin,gpio.HIGH)
            gpio.output(pulse_pin2,gpio.HIGH)
            sleep(.001)
            gpio.output(pulse_pin,gpio.LOW)
            gpio.output(pulse_pin2,gpio.LOW)
            sleep(.0005)
            z_step_count+=1
        
        log.write(f"(Step in Z axis is {z_step_count}\n")
        gpio.output(Green_led_static,gpio.LOW) # Green led off
        z_max = z_step_count
        sleep(1)
        
        gpio.output(direction_pin,ccw_direction) # towards motors
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
            
        log.write("Re-Home cycle2\n")
        gpio.output(direction_pin,cw_direction)
        gpio.output(direction_pin2,cw_direction)

        if(gpio.input(x_axis_limit)!=0):
            for x in range(move_out_steps_max_X):
                gpio.output(pulse_pin,gpio.HIGH)
                gpio.output(pulse_pin2,gpio.HIGH)
                sleep(.001)
                gpio.output(pulse_pin,gpio.LOW)
                gpio.output(pulse_pin2,gpio.LOW)
                sleep(.0005)
            sleep(1)
            
        while(gpio.input(x_axis_limit) == 0):
            gpio.output(pulse_pin,gpio.HIGH)
            gpio.output(pulse_pin2,gpio.HIGH)
            sleep(.001)
            gpio.output(pulse_pin,gpio.LOW)
            gpio.output(pulse_pin2,gpio.LOW)         
            sleep(.0005)
            
        log.write('X axis is at X Home position second time\n')
        sleep(1)

        gpio.output(direction_pin,ccw_direction)
        gpio.output(direction_pin2,ccw_direction)
        
        # move away from start
        if(gpio.input(x_axis_limit)!=0):
            for x in range(move_out_steps_max_X):
                gpio.output(pulse_pin,gpio.HIGH)
                gpio.output(pulse_pin2,gpio.HIGH)
                sleep(.001)
                gpio.output(pulse_pin,gpio.LOW)
                gpio.output(pulse_pin2,gpio.LOW)
                sleep(.0005)
            sleep(1)

        gpio.output(direction_pin,cw_direction)# away from motors
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
        
        gpio.output(direction_pin,ccw_direction)# away from motors
        gpio.output(direction_pin2,cw_direction)
        
        log.write("Move to Z axis home second time\n")
        while(gpio.input(z_axis_limit)==0):
            gpio.output(pulse_pin,gpio.HIGH)
            gpio.output(pulse_pin2,gpio.HIGH)
            sleep(.001)
            gpio.output(pulse_pin,gpio.LOW)
            gpio.output(pulse_pin2,gpio.LOW)
            sleep(.0005)
        
        log.write('Z axis in home position\n')
        sleep(1)

        gpio.output(direction_pin,cw_direction)
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
        log.write("Y axis is at Home position\n")
               
        log.write("Y axis calibration\n")
        gpio.output(direction_pinY,ccw_direction)
        if(gpio.input(y_axis_limit)!=0):
            for x in range(move_out_steps_max_Y):
                gpio.output(pulse_pinY,gpio.HIGH)
                sleep(0.001)
                gpio.output(pulse_pinY,gpio.LOW)
                sleep(0.0005)
            sleep(1)
            
        while(gpio.input(y_axis_limit)==0):
            gpio.output(pulse_pinY,gpio.HIGH)
            sleep(0.001)
            gpio.output(pulse_pinY,gpio.LOW)
            sleep(0.0005)
            y_step_count+=1
        sleep(1)
        
        y_max = y_step_count 
        log.write(f"Y axis max steps {y_max}\n")
        
        gpio.output(direction_pinY,cw_direction)
        if(gpio.input(y_axis_limit)!=0):
            for x in range(move_out_steps_max_Y):
                gpio.output(pulse_pinY,gpio.HIGH)
                sleep(0.001)
                gpio.output(pulse_pinY,gpio.LOW)
                sleep(0.0005)
            sleep(1)
        

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
        
        if(x_max > 900 and z_max > 1900):
            log.write("Writing Calibration data\n")
            t = datetime.datetime.now()
            FileName = CreateFileName(t)
            calibrationFile = open(FileName,"w")
            currentCalFile = open(CurrentCalibration_File_Name,"w")
            header = "DateTime,X_Max,Y_Max,Z_Max\n"
            calibrationFile.write(header)
            currentCalFile.write(header) # used to allow calibration to be re-used
            CalLine = f"{t},{x_max},{y_max},{z_max}\n"
            calibrationFile.write(CalLine)
            currentCalFile.write(CalLine)
            calibrationFile.close()
            currentCalFile.close()
        else:
            log.write("Using default calibration data\n")
            if x_max < 900:
                x_max = 1250
            if z_max < 1900:
                z_max = 2800
            if y_max < 1200:
                y_max = 1530
            t = datetime.datetime.now()
            FileName = CreateFileName(t)
            calibrationFile = open(FileName,"w")
            currentCalFile = open(CurrentCalibration_File_Name,"w")
            header = "DateTime,X_Max,Y_Max,Z_Max\n"
            calibrationFile.write(header)
            currentCalFile.write(header) # used to allow calibration to be re-used
            CalLine = f"{t},{x_max},{y_max},{z_max}\n"
            calibrationFile.write(CalLine)
            currentCalFile.write(CalLine)
            calibrationFile.close()
            currentCalFile.close()
        
        for b in range(6 ):
            gpio.output(Green_led_dynamic,gpio.HIGH) # Green led on
            sleep(0.25)
            gpio.output(Green_led_dynamic,gpio.LOW) # Green led off
            sleep(0.25)
         
        log.write("At Home postion now\n")
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
        
        for b in range(10):
            gpio.output(Green_led_dynamic,gpio.HIGH) # Green led on
            sleep(0.5)
            gpio.output(Green_led_dynamic,gpio.LOW) # Green led off
            sleep(0.5)
            
        cycle=False
        log.write("Calibration End\n")
        log.close()
        exit()
        
except KeyboardInterrupt:
    gpio.cleanup()
