from time import sleep
import time

import RPi.GPIO as gpio
import math
import csv
import datetime

import os
import shutil
import socket

# GPIO variables for Raspberry Pi for stepper motor drivers (Jasmine label each one, or change names to motor a,b,y)
# 11/08/24 motor A dir 19, pulse 26
# 11/08/24 motor B, dir 21, pul 20
direction_pin   = 21 # motor a
pulse_pin       = 20
direction_pin2  = 19 # motor b
pulse_pin2      = 26
direction_pinY  = 13 # motor y
pulse_pinY      = 6
# Variables for directions of all motors
cw_direction    = 0 
ccw_direction   = 1
# GPIO varibales for RPi limit switches
x_axis_limit    = 17
z_axis_limit    = 27
y_axis_limit    = 22
# GPIO variables for LEDs: dynamic is LED on tower, static are leds on saccade rod
Green_led_dynamic = 23
Green_led_static = 24

#GPIO variables for Emergency Stop switch sense
em_stop_sense_normal = 4 # emergency stop switch sensing high 2.4volts (logic 1 or high) when operation normally 24 power on when low emergency stop is pressed
em_stop_sense_stopped = 5 # when high 2.4 volts (logic 1 or high) emergency stip button has been press and is activewhen low operation is normal ok


# GPIO set up for output: motors
gpio.setmode(gpio.BCM)
gpio.setwarnings(False)
gpio.setup(direction_pin, gpio.OUT)
gpio.setup(direction_pin2, gpio.OUT)
gpio.setup(direction_pinY, gpio.OUT)

gpio.setup(pulse_pin, gpio.OUT)
gpio.setup(pulse_pin2, gpio.OUT)
gpio.setup(pulse_pinY, gpio.OUT)
# GPIO set up for input: limit switches           
gpio.setup(x_axis_limit, gpio.IN)
gpio.setup(z_axis_limit, gpio.IN)
gpio.setup(y_axis_limit, gpio.IN)
# GPIO output for LEDs
gpio.setup(Green_led_dynamic, gpio.OUT)
gpio.setup(Green_led_static, gpio.OUT)

gpio.output(direction_pin,cw_direction) # left motor (A)
gpio.output(direction_pin2,ccw_direction) # right motor (b)
gpio.output(direction_pinY,cw_direction) # y axis motor

#emergency stop switch sensing connection setup
gpio.setup(em_stop_sense_normal,gpio.IN)
gpio.setup(em_stop_sense_stopped, gpio.IN)


##########################################################################################
# global variable initialisation
cycle=True
# delete???
x_step_count=0
z_step_count=0
y_step_count=0

# global variables for calibration steps
x_max = -1
z_max = -1
y_max = -1

# buffer distance to make sure that limit switches have no pressure on them and untoggle them
# as of 08/08/2024 step sizes: 0.31mm linear for x and z and ___? for y 
move_out_steps_max_X = 20
move_out_steps_max_Z = 20
move_out_steps_max_Y = 20

# IP address for socket
IP_address = "127.0.0.1"

# setting directories and folder paths
Current_dir = "/home/emitd/src/python/RasberryPiEmitd"
os.chdir(Current_dir)
Calibration_File_Name_start  = "CalFile"
Calibration_File_Name_suffix = "cal"
CurrentCalibration_File_Name = "CurrentCalib.cal"
Log_File_Path    = os.path.join(Current_dir, "log")
Input_File_Path  = os.path.join(Current_dir, "input_files")
Output_File_Path = os.path.join(Current_dir, "output_files")
Data_File_Path   = os.path.join(Current_dir, "data_files")
Backup_File_Path = os.path.join(Current_dir, ".backup")

# global variables for business logic so that routine can be kept track of and saccade rod/quit prompts/messages can be made
Total_Number_Of_Files = -1
Current_Block_Number = -1

#****************************************************************************************************#
# Classes
# object class to store initial robot target position when using constructor (__init__), to be used for calculating dist/angles with new target position
class target_position:
    X = 0
    Y = 0
    Z = 0
    
    def __init__ ( self, x,y,z): # constructor
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
        
# can this be deleted? Not used
class Led_time_state:
    led_number:int = 0 # led 1 = static, led 2 = dynamic
    led_state:int = 0   # off = 0 on = 1
    timeSliceNumber:int = 0 # number of steps for start of sequence
    
    def __init__ (self,led_no,state,sliceNumber):
        self.led_number = led_number
        self.led_state = state
        self.timeSliceNumber = sliceNumber
        
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#\
# Functions

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
    
    # set direction and work out x and z
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
        if(gpio.input(x_axis_limit) == 0 and gpio.input(z_axis_limit) == 0 and gpio.input(em_stop_sense_normal)==1 ):
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
        if gpio.input(y_axis_limit) == 0 and gpio.input(em_stop_sense_normal)==1 :
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

def CreateDataFileName(x: datetime, experimentCode, particpant):
    year  = x.year
    month = x.month
    day   = x.day
    hr    = x.hour
    mins  = x.minute
    sec   = x.second
    result = f"{Data_File_Path}//RealData_{year}{month}{day}T{hr}{mins}{sec}_{experimentCode}_{particpant}.csv"
    return result

def CreateBackupFileName(x: datetime, experimentCode, particpant):
    year  = x.year
    month = x.month
    day   = x.day
    hr    = x.hour
    mins  = x.minute
    sec   = x.second
    result = f"{Backup_File_Path}//RealData_{year}{month}{day}T{hr}{mins}{sec}_{experimentCode}_{particpant}.csv"
    return result

def CreateInputFileName(Input_File_Path, FileName): # untested move this code to working code 
    filename = os.path.basename(FileName)
    result= f"{Input_File_Path}//{filename}"
    return result

def CreateOutputFileName(Output_File_Path,FileName): # untested move this code to working code
    filename = os.path.basename(FileName)
    result= f"{Output_File_Path}//{filename}"
    return result

def CreateDataFile(dataFileName:str):
    #("trial_num,blockNum,participant,visualAngle,viewingDistance,static_x,static_y,static_z,dynamic_x,dynamic_y,dynamic_z,led1on1,led2on,led1off1,led1on2,led2off,led1off2,");
    header = "experimentCode,trial_num,block_num,participant,visualAngle,viewingDistance,static_x,static_y,static_z,dynamic_x,dynamic_y,dynamic_z,led1on1,led2on,led1off1,led1on2,led2off,led1off2,\n"
    datafile = open(dataFileName,"w")
    datafile.write(header)
    return datafile

# function to slice up saccade experiment and time the leds turning on and off, and write to data file
def Led_Sequencer(blink : int, dwell : int, gap : int,saccade_position : target_position, current_position : target_position, datafile,log,experimentCode,trial,block,participant,visualangle,viewingDistance):
    led_time_states: led_time_state = [] # can we delete this?
    led1 = Green_led_static # saccad rod led
    led2 = Green_led_dynamic # dynamic led
    seq_time = 12.5 #total saccad time
    time_slice = 0.1 #time increments where all changes occur,
    steps = math.ceil(seq_time/time_slice)
    time_slice_converted = time_slice * 1000  # times 1000 to account for the arguments being parsed as milliseconds to avoid rounding errors .

    # fill the led_times_states list here
     
    # algorithm for fixation and gap time, gap time is negative for an overlap and positive for a gap 
    # blink offsets the start time    
    # fixation from Saccade_Instruction class: dwell
    # gap from Saccade_Instruction class: gap   
    sequence = []
    sequence.append(int(blink/4 * 0 / time_slice_converted))                    #led1 on 0
    sequence.append(int(blink/4 * 1 / time_slice_converted))                    #led1 off 2
    sequence.append(int(blink/4 * 2 / time_slice_converted))                    #led1 on 4
    sequence.append(int(blink/4 * 3 / time_slice_converted))                    #led1 off 6
    sequence.append(int(blink / time_slice_converted))                          #led1 on 8
    sequence.append(int((dwell + gap + blink) / time_slice_converted ))         #led2 on 46
    sequence.append(int(((dwell + blink) / time_slice_converted)))                #led1 off 48
    sequence.append(int((2*dwell + 2*gap + blink) / time_slice_converted))      #led1 on 84
    sequence.append(int((2*dwell + gap + blink) / time_slice_converted))        #led2 off 86
    sequence.append(int((3*dwell + 2*gap + blink) / time_slice_converted))      #led1 off 124
    ts = [] # list of timestamps from this saccade trial
    
    for t in range(steps): # time increments is t
        if t == sequence[0] or t == sequence[2]:
            gpio.output(led1,gpio.HIGH)
            log.write(f"led1 on step {t}\n")

        elif t == sequence[1] or t == sequence[3]:
            gpio.output(led1,gpio.LOW)
            log.write(f"led1 off step {t}\n")
            
        elif t == sequence[4]:
            gpio.output(led1,gpio.HIGH)
            tstamp = time.time()
            ts_string = repr(tstamp)
            ts.append(ts_string)
            log.write(f"led1on1 on step {t}\n")
            
        elif t == sequence[5]:
            gpio.output(led2,gpio.HIGH)
            tstamp = time.time()
            ts_string = repr(tstamp)
            ts.append(ts_string)
            log.write(f"led2on1 step {t}\n")
        
        elif t == sequence[6]:
            gpio.output(led1,gpio.LOW)
            tstamp = time.time()
            ts_string = repr(tstamp)
            ts.append(ts_string)
            log.write(f"led1off1 step {t}\n")
            
        elif t == sequence[7]:
            gpio.output(led1,gpio.HIGH)
            tstamp = time.time()
            ts_string = repr(tstamp)
            ts.append(ts_string)
            log.write(f"led1on2 step {t}\n")
            
        elif t == sequence[8]:
            gpio.output(led2,gpio.LOW)
            tstamp = time.time()
            ts_string = repr(tstamp)
            ts.append(ts_string)
            log.write(f"led2off step {t}\n")
            
        elif t == sequence[9]:
            gpio.output(led1,gpio.LOW)
            tstamp = time.time()
            ts_string = repr(tstamp)
            ts.append(ts_string)
            log.write(f"led1off2 step {t}\n")
            
        sleep(time_slice)
    
    # write data with timestamp list for each led turning on and off
    data_line = Format_Log_Data_Line(current_position,saccade_position,ts,experimentCode,trial,block,participant,visualangle,viewingDistance)
    datafile.write(data_line)
    datafile.flush()
    os.fsync(datafile)
    
    return 0

#trial_num,blockNum,participant,visualAngle,viewingDistance,static_x,static_y,static_z,dynamic_x,dynamic_y,dynamic_z,led1on1,led2on,led1off1,led1on2,led2off,led1off2
# change to experiment code
# Creates one line of the robot data to write to file
def Format_Log_Data_Line(currentPosition, saccade_position,timestamplist,experimentCode,trialNo,blockNo,Participant,Visualangle,ViewingDistance):
    # change to Experiment code eg. RSAC[F-B][1-3] Real Saccade Front/Back Position 1|2|3 
    static_x  = saccade_position.X
    static_y  = saccade_position.Y
    static_z  = saccade_position.Z
    dynamic_x = currentPosition.X
    dynamic_y = currentPosition.Y
    dynamic_z = currentPosition.Z
    led1on1  = timestamplist[0]
    led2on   = timestamplist[1]
    led1off1 = timestamplist[2]
    led1on2  = timestamplist[3]
    led2off  = timestamplist[4]
    led1off2 = timestamplist[5]
    result = f"{experimentCode},{trialNo},{blockNo},{Participant},{Visualangle},{ViewingDistance},{static_x},{static_y},{static_z},{dynamic_x},{dynamic_y},{dynamic_z},{led1on1},{led2on},{led1off1},{led1on2},{led2off},{led1off2},\n"
    return result

# networking for syncing Tobii
def Signal_Unity_On():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = 56712
        
        sock.connect((IP_address, port))
    
        sock.sendall(b"ToggleOn")
    
        sock.close()
    except:
        print("exception occured trying to signal Unity")
    finally:
        return 0
    
def Signal_Unity_Off():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        port = 56712
        
        sock.connect((IP_address, port))
    
        sock.sendall(b"ToggleOff")
    
        sock.close()
    except:
        print("exception occured trying to signal Unity")
    finally:
        return 0
# -----------------------------------------------------------------------------------------#
# Main routine starts here
try:
    # turn leds off in case they were left on
    gpio.output(Green_led_dynamic,gpio.LOW)
    gpio.output(Green_led_static,gpio.LOW)
    if(gpio.input(em_stop_sense_normal)!= 1):
        print("Emergency stop button active or 24 volt power supply is not on")
        print("Exiting program please rectify the problem")
        exit()
    # Creating log files
    logstart = datetime.datetime.now()
    logFileName = CreateLogFileName(logstart)
    # "w" is for write
    log = open(logFileName,"w")
    print(f"Running Trials at {logstart}")
    # start up queries to ensure user will safely operate machine
    confirm = False
    while not confirm:
        response = input("Please confirm Saccade Rod is removed from the Robot (Y/N)")
        log.write(f"Comfirmed Saccade Rod Removed {response}\n")
        if(response.startswith("y") or response.startswith("Y")):
            confirm = True
        else:
           print("Invalid response please enter (Y/N) after removing the saccade rod from the Robot")
           log.write("Invalid response recieved ask again\n")
    
    # while cycle is true, file will be read and trial block will be executed,
    # cycle will be false when csv reaches "end"
    # X HOMING
    while cycle== True:
        log.write("Home Axis\n")
        log.write('X axis move to start posn\n')
        gpio.output(direction_pin,cw_direction)
        gpio.output(direction_pin2,cw_direction)
        
        # check first that limit switch is not being touched, move out if it is
        if(gpio.input(x_axis_limit)!=0 and gpio.input(em_stop_sense_normal)==1 ):
            for x in range(move_out_steps_max_X):
                gpio.output(pulse_pin2,gpio.HIGH)
                gpio.output(pulse_pin,gpio.HIGH)
                sleep(.001)
                gpio.output(pulse_pin2,gpio.LOW)
                gpio.output(pulse_pin,gpio.LOW)
                sleep(.0005)
            sleep(1)
            
        gpio.output(Green_led_dynamic,gpio.HIGH) # Green led on
        
        # home to x limit switch, to the right/towards motor A; until limit switch pressed
        while(gpio.input(x_axis_limit) == 0 and gpio.input(em_stop_sense_normal)==1 ):
            gpio.output(pulse_pin2,gpio.HIGH)
            gpio.output(pulse_pin,gpio.HIGH)
            sleep(.001)
            gpio.output(pulse_pin2,gpio.LOW)
            gpio.output(pulse_pin,gpio.LOW)         
            sleep(.0005)
        log.write('X axis is at X Home position\n')
        gpio.output(Green_led_dynamic,gpio.LOW) # Green led off
        sleep(1)
        # change direction to move away from limit switch
        gpio.output(direction_pin2,ccw_direction)
        gpio.output(direction_pin,ccw_direction)
        
        # move away from home position (away from limit switch by certain number of steps)
        if(gpio.input(x_axis_limit)!=0 and gpio.input(em_stop_sense_normal)==1 ):
            for x in range(move_out_steps_max_X):
                gpio.output(pulse_pin2,gpio.HIGH)
                gpio.output(pulse_pin,gpio.HIGH)
                sleep(.001)
                gpio.output(pulse_pin2,gpio.LOW)
                gpio.output(pulse_pin,gpio.LOW)
                sleep(.0005)
            sleep(1)
            
        # Z HOMING
        log.write("Z axis home cycle\n")
        gpio.output(direction_pin,ccw_direction) # to motors
        gpio.output(direction_pin2,cw_direction)
        
        if(gpio.input(z_axis_limit)!=0 and gpio.input(em_stop_sense_normal)==1 ):
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
        while(gpio.input(z_axis_limit)==0 and gpio.input(em_stop_sense_normal)==1 ):
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
        
        if(gpio.input(z_axis_limit)!=0 and gpio.input(em_stop_sense_normal)==1 ):
            for x in range(move_out_steps_max_Z):
                gpio.output(pulse_pin,gpio.HIGH)
                gpio.output(pulse_pin2,gpio.HIGH)
                sleep(.001)
                gpio.output(pulse_pin,gpio.LOW)
                gpio.output(pulse_pin2,gpio.LOW)
                sleep(.0005)
            sleep(1)
        # Y HOMING                
        log.write("Y axis calibration move to home position\n")
        gpio.output(direction_pinY,cw_direction)
        if(gpio.input(y_axis_limit)!=0 and gpio.input(em_stop_sense_normal)==1 ):
            for x in range(move_out_steps_max_Y):
                gpio.output(pulse_pinY,gpio.HIGH)
                sleep(0.001)
                gpio.output(pulse_pinY,gpio.LOW)
                sleep(0.0005)
            sleep(1)
            
        gpio.output(direction_pinY,cw_direction)    
        while(gpio.input(y_axis_limit)==0 and gpio.input(em_stop_sense_normal)==1 ):
            gpio.output(pulse_pinY,gpio.HIGH)
            sleep(0.001)
            gpio.output(pulse_pinY,gpio.LOW)
            sleep(0.0005)
        sleep(1)
        
        gpio.output(direction_pinY,ccw_direction)
        if(gpio.input(y_axis_limit)!=0 and gpio.input(em_stop_sense_normal)==1 ):
            for x in range(move_out_steps_max_Y):
                gpio.output(pulse_pinY,gpio.HIGH)
                sleep(0.001)
                gpio.output(pulse_pinY,gpio.LOW)
                sleep(0.0005)
            sleep(1)
        log.write("Y axis is at Home position\n")
        log.flush()
        log.write("Reading Calibration file {CurrentCalibration_File_Name}\n")
        # opening calibration file to get last calibration data
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
        # change this to account for changes in motor steps sizes
        if x_max > 900 and z_max > 1900 and y_max > 1200:
            log.write("Calibration appears to be good\n")
        else:
            log.write("calibration is invalid one or more axis are not calibrated correctly\n")
            log.write("Please re-calibrate\n")
            log.write("Exiting program now\n")
            print("calibration is invalid one or more axis are not calibrated correctly")
            print("Please re-calibrate")
            print("Exiting program now")
            log.close()
            exit(-1)
        for b in range(4):
            gpio.output(Green_led_dynamic,gpio.HIGH) # Green led on
            sleep(0.25)
            gpio.output(Green_led_dynamic,gpio.LOW) # Green led off
            sleep(0.25)
         
        log.write("At Home now ready and calibrated\n")
        
        # Move to halfway point for each axis before start of trial (helps to avoid sticking in the limit switches
        current = target_position(0,0,0)
        newposition = target_position(math.floor(x_max/2),0,0)
        start = time.time()
        move_to_position(newposition,current,0.001)
        end = time.time()
        log.write(f"x move time {end - start}\n")
        current = newposition
        log.write(f" Postion is X = {current.X} Y= {current.Y} = {current.Z}\n")
        start = time.time()
        nextposition=target_position(math.floor(x_max*0.5),0,math.floor(z_max*0.5))
        move_to_position(nextposition,current,0.001)
        end = time.time()
        log.write(f"z move time {end - start}\n")
        current = nextposition
        log.write(f" Postion is X = {current.X} Y= {current.Y} = {current.Z}\n")
        # change name to midpoint pos for clarity
        nextposition=target_position(math.floor(x_max*0.5),math.floor(y_max*0.5),math.floor(z_max*1))
        move_to_position(nextposition,current,0.001)
        current = nextposition
        log.write(f" Postion is X = {current.X} Y= {current.Y} = {current.Z}\n")
        log.flush()
        os.fsync(log)
        # Now is the time to put in the saccade rod safely
        confirm2 = False
        while not confirm2:
            response = input("Please insert the Saccade rod in the desired position(Y/N)")
            log.write(f"Comfirmed Saccade rod is inserted {response}\n")
            if(response.startswith("y") or response.startswith("Y")):
                confirm2 = True
            else:
               print("Invalid response please enter (Y/N) after inserting the Saccade rod in the Robot")
               log.write("Invalid response recieved ask again\n")
        #get all the input file name
        #input_file_path = "home/emitd/src/python/RasberryPiEmitd"
        my_file_list = []
        for file in os.listdir(Input_File_Path): # probably a bug here
            if file.endswith(".txt"):
               full_path = os.path.join(Input_File_Path, file) 
               my_file_list.append(full_path)
               log.write(f"Adding file {file} to list of files for trial\n")
               
        log.flush()
        os.fsync(log)
        
        # iterating through each line of csv and executing move to target and then led sequence and then writing to files
        Total_Number_Of_Files = len(my_file_list)
        current_file_number = 0
        for my_file in my_file_list:
            current_file_number+=1
            with open(my_file) as file:
                heading = next(file)
                reader = csv.reader(file)
                rowNumber = 0
                for row in reader:
                    log.write(f"Current position {current.X}, {current.Z}\n")
                    if row[0]!="end":
                        #DoTo: read input csv paramters
                        expCode = row[0]
                        blockNum = row[1]
                        Current_Block_Number = blockNum
                        trialNum = row[2]
                        partCode = row[3]
                        visualAngle = row[4]
                        viewingDistance = row[5]
                        staticX = row[6]
                        staticY = row[7]
                        staticZ = row[8]
                        sx_position = math.floor(float(staticX)*x_max) 
                        sy_position = math.floor(float(staticY)*y_max)
                        sz_position = math.floor(float(staticZ)*z_max)
                        staticPosition = target_position(sx_position,sy_position,sz_position)
                        dynamicX = row[9]
                        dynamicY = row[10]
                        dynamicZ = row[11]
                        staticCol = row[12]
                        dynamicCol = row[13]
                        blink = int(row[14])
                        dwell = int(row[15])
                        gap = int(row[16])
                        
                        # if first row, make new file
                        if rowNumber == 0:
                            dateTime = datetime.datetime.now()
                            DataFileName = CreateDataFileName(dateTime, expCode, partCode)
                            BackupFileName = CreateBackupFileName(dateTime, expCode, partCode)
                            datafile = CreateDataFile(DataFileName)
                            
                        # converting unity positions into motor steps    
                        x_position = math.floor(float(dynamicX)*x_max) # wrong way for 0.4 -- went left, should have been right
                        y_position = math.floor(float(dynamicY)*y_max)
                        z_position = math.floor(float(dynamicZ)*z_max) # correct way for 0.6 -- went back
                        
                        log.write(f" Position is X = {current.X} Y= {current.Y} = {current.Z}\n")
                        #wait_time = int(row[7])/1000
                        # change nextpos to other name
                        nextPosition2 = target_position(x_position,y_position,z_position)
                        if nextPosition2.Z == z_max and nextPosition2.X != current.X:
                            transitionPosition1 = target_position(current.x,current.y,math.floor(0.75*z_max))
                            transitionPosition2 = target_position(nextPosition2.x, nextPosition2.y,floor(0.75*z_max))
                            move_to_position(transitionPosition1,current,0.001)
                            current = transitionPosition1
                            move_to_position(transitionPosition2,current,0.001)
                            current = transitionPosition2
                        move_to_position(nextPosition2,current,0.001)
                        current=nextPosition2
                        #def Led_Squencer(blink : int, dwell : int, gap : int, current_position : target_position
                        log.write(f"blink: {blink} dwell: {dwell} gap {gap}\n")
                        #Signal_Unity_On()
                        #blink : int, dwell : int, gap : int, static_position : target_position, current_position : target_position, datafile,log,experimentCode,trial,block,participant,visualangle,viewingDistance
                        Led_Sequencer(blink,dwell,gap,staticPosition, current, datafile, log, expCode, trialNum, blockNum, partCode, visualAngle, viewingDistance)
                        #Signal_Unity_Off()
                        sleep(0.2)
                        rowNumber+=1
                        if(gpio.input(em_stop_sense_normal)!=1 and gpio.input(em_stop_sense_stopped)!=0):
                            print("Emergency stop sensed exiting program")
                            exit()
                        
                        
                    else: # if file is complete, copy data file to backup
                        datafile.close()
                        shutil.copy(DataFileName,BackupFileName)
                
                # moving input file to output so that file becomes empty as routine is being completed
                inputfilename = CreateInputFileName(Input_File_Path,file)
                outputfilename = CreateOutputFileName(Output_File_Path,file)
                shutil.move(inputfilename,outputfilename)
                log.flush()
                os.fsync(log)
                if gpio.input(em-stop-sense-normal)!=1 and gpio.input(em-stop-sense-stopped)!=0:
                    print("Emergency stop sensed exiting program")
                    exit()
                    
                
                #ToDo: prompt to continue here
                print("Block complete ")
                if Current_Block_Number == 3 and current_file_number ==3:
                    res3 = False
                    while res3 == False:
                        response3 = input("Please re-position the saccade rod and enter (Y/N) to continue or (Q) to exit the experiment")
                        log.write(f"Response at block end {Current_Block_Number} file number {current_file_number} is {response3}\n")
                        if response3 == 'y' or response3 == 'Y':
                            res3=True
                        elif response3 == 'q' or response3 == 'Q':
                            log.close()
                            exit()
                elif Current_Block_Number == 3 and current_file_number == 6:
                    print("Experiment is complete")
                    continue
                else:
                    res4 = False
                    while res4 == False:
                        response4 = input("Please enter (Y/N) to continue or (Q) to exit the experiment")
                        log.write(f"Respone at block end {Current_Block_Number} file number {current_file_number} is {response4}\n")
                        if response4 == 'y' or response4 == 'Y':
                            res4=True
                        elif response4 == 'q' or response4 == 'Q':
                            log.close()
                            exit()

                
        log.close()
        for b in range(10):
            gpio.output(Green_led_dynamic,gpio.HIGH) # Green led on
            sleep(0.5)
            gpio.output(Green_led_dynamic,gpio.LOW) # Green led off
            sleep(0.5)
            
        cycle=False
        print(" cycle end")
        gpio.cleanup()
        exit()

# CTRL + C, will terminate programme at any point
except KeyboardInterrupt:
    log.write("Keyboard interrupt occured\n")
    log.close()
    gpio.cleanup()
