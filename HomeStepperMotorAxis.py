from time import sleep
import time
import RPi.GPIO as gpio
import math
import csv

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

Green_led       = 23


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

gpio.setup(Green_led, gpio.OUT)

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
            
    
try:
    while cycle== True:
        print("Home cycle 1 start")
        sleep(2)
        print('X axis move to start posn')
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
            
        gpio.output(Green_led,gpio.HIGH) # Green led on
        
        while(gpio.input(x_axis_limit) == 0):
            gpio.output(pulse_pin2,gpio.HIGH)
            gpio.output(pulse_pin,gpio.HIGH)
            sleep(.001)
            gpio.output(pulse_pin2,gpio.LOW)
            gpio.output(pulse_pin,gpio.LOW)         
            sleep(.0005)
        print('X axis is at X Home position')
        gpio.output(Green_led,gpio.LOW) # Green led off
        sleep(1)
        print('X axis move to end posn to determin max steps')
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
        gpio.output(Green_led,gpio.HIGH) # Green led on    
        while(gpio.input(x_axis_limit) == 0):
            gpio.output(pulse_pin2,gpio.HIGH)
            gpio.output(pulse_pin,gpio.HIGH)
            sleep(.001)
            gpio.output(pulse_pin2,gpio.LOW)
            gpio.output(pulse_pin,gpio.LOW)
            sleep(.0005)
            x_step_count+=1
            
        print(f"Steps in X axis is {x_step_count}")
        gpio.output(Green_led,gpio.LOW) # Green led off
        x_max=x_step_count
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
        
        print("Z axis home cycle")
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
        
        gpio.output(Green_led,gpio.HIGH) # Green led on
        print("Move to Z axis home")
        while(gpio.input(z_axis_limit)==0):
            gpio.output(pulse_pin,gpio.HIGH)
            gpio.output(pulse_pin2,gpio.HIGH)
            sleep(.001)
            gpio.output(pulse_pin,gpio.LOW)
            gpio.output(pulse_pin2,gpio.LOW)
            sleep(.0005)
        
        print('Z axis in home position')
        sleep(1)
        gpio.output(Green_led,gpio.LOW) # Green led off
        
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
            
        print("Move to Z axis end")
        gpio.output(Green_led,gpio.HIGH) # Green led on
        while(gpio.input(z_axis_limit)==0):
            gpio.output(pulse_pin,gpio.HIGH)
            gpio.output(pulse_pin2,gpio.HIGH)
            sleep(.001)
            gpio.output(pulse_pin,gpio.LOW)
            gpio.output(pulse_pin2,gpio.LOW)
            sleep(.0005)
            z_step_count+=1
        
        print(f"(Step in Z axis is {z_step_count}")
        gpio.output(Green_led,gpio.LOW) # Green led off
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
            
        print ("Re-Home cycle2")
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
            
        print('X axis is at X Home position second time')
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
        
        print("Move to Z axis home second time")
        while(gpio.input(z_axis_limit)==0):
            gpio.output(pulse_pin,gpio.HIGH)
            gpio.output(pulse_pin2,gpio.HIGH)
            sleep(.001)
            gpio.output(pulse_pin,gpio.LOW)
            gpio.output(pulse_pin2,gpio.LOW)
            sleep(.0005)
        
        print('Z axis in home position')
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
        
        if x_max == 900:
            x_max = 1260
        
        if z_max > 1900:
            z_max = 2824
        
        for b in range(10):
            gpio.output(Green_led,gpio.HIGH) # Green led on
            sleep(0.5)
            gpio.output(Green_led,gpio.LOW) # Green led off
            sleep(0.5)
         
        print("At Home now ready")
        current = target_position(0,0,0)
        newposition = target_position(math.floor(x_max/2),0,0)
        start = time.time()
        move_to_position(newposition,current,0.001)
        end = time.time()
        print(f"x move time {end - start}")
        current = newposition
        print(current.X, current.Z)
        start = time.time()
        nextposition=target_position(math.floor(x_max/2),0,math.floor(z_max/2))
        move_to_position(nextposition,current,0.001)
        end = time.time()
        print(f"z move time {end - start}")
        current = nextposition
        print(current.X, current.Z)
        
        with open(csv_file) as file:
            heading = next(file)
            reader = csv.reader(file)
            for row in reader:
                print(current.X, current.Z)
                if row[0]!="end":
                    x_position = math.floor(float(row[4])*x_max) # wrong way for 0.4 -- went left, should have been right
                    z_position = math.floor(float(row[5])*z_max) # correct way for 0.6 -- went back
                    print(x_position,z_position)
                    wait_time = int(row[7])/1000
                    nextposition2 = target_position(x_position,0,z_position)
                    move_to_position(current,nextposition2,0.001)
                    current=nextposition2
                    sleep(wait_time)
                
        print("Done csv commands")
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
