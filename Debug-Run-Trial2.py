from time import sleep
import time

import RPi.GPIO as gpio
import math
import csv
import datetime

import os
import shutil
import socket

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

IP_address = "127.0.0.1"
#Current_Dir = "/home/emitd/src/python/RasberryPiEmitd"
#os.chdir(Current_Dir)
Calibration_File_Name_start  = "CalFile"
Calibration_File_Name_suffix = "cal"
CurrentCalibration_File_Name = "CurrentCalib.cal"
Log_File_Path    = ".//log"
Input_File_Path  = ".//input_files"
Output_File_Path = ".//output_files"
Data_File_Path   = ".//data_files"
Backup_File_Path = ".//.backup"

Total_Number_Of_Files = -1
Current_Block_Number = -1

 
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



def Led_Sequencer(blink : int, dwell : int, gap : int,saccade_position : target_position, current_position : target_position, datafile,log,experimentCode,trial,block,participant,visualangle,viewingDistance):
    led_time_states: led_time_state = []
    led1 = Green_led_static # saccad rod led
    led2 = Green_led_dynamic # dynamic led
    seq_time = 12.5 #total saccad time
    time_slice = 0.1 #time increments where all changes occur,
    steps = math.ceil(seq_time/time_slice)
    time_slice = time_slice * 1000  # times 1000 to account for the arguments being parsed as milliseconds to avoid rounding errors .

    # fill the led_times_states list here
     
    # algorithm for fixation and gap time, gap time is negative for an overlap and positive for a gap 
    # blink offsets the start time    
    # fixation from Saccade_Instruction class: dwell
    # gap from Saccade_Instruction class: gap   
    sequence = []
    sequence.append(int(blink/4 * 0 / time_slice))                    #led1 on 0
    sequence.append(int(blink/4 * 1 / time_slice))                    #led1 off 2
    sequence.append(int(blink/4 * 2 / time_slice))                    #led1 on 4
    sequence.append(int(blink/4 * 3 / time_slice))                    #led1 off 6
    sequence.append(int(blink / time_slice))                          #led1 on 8
    sequence.append(int((dwell + gap + blink) / time_slice ))         #led2 on 46
    sequence.append(int(((dwell + blink) / time_slice)))                #led1 off 48
    sequence.append(int((2*dwell + 2*gap + blink) / time_slice))      #led1 on 84
    sequence.append(int((2*dwell + gap + blink) / time_slice))        #led2 off 86
    sequence.append(int((3*dwell + 2*gap + blink) / time_slice))      #led1 off 124
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
            
        sleep(0.1)
    
    data_line = Format_Log_Data_Line(current_position,saccade_position,ts,experimentCode,trial,block,participant,visualangle,viewingDistance)
    datafile.write(data_line)
    datafile.flush()
    os.fsync(datafile)
    
    return 0

#trial_num,blockNum,participant,visualAngle,viewingDistance,static_x,static_y,static_z,dynamic_x,dynamic_y,dynamic_z,led1on1,led2on,led1off1,led1on2,led2off,led1off2
# change to experiment code 
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
    
def Signal_Unity_On():
    try:
        sock = socket.socket(socket.AF_INET, socket.socket_StREAM)
        port = 56712
    
        sock.connect(IP_address,port)
    
        sock.sendall(b"ToggleOn")
    
        sock.close()
    except:
        print("exception occured trying to signal Unity")
    finally:
        return 0
    
def Signal_Unity_Off():
    try:
        sock = socket.socket(socket.AF_INET, socket.socket_StREAM)
        port = 56712
    
        sock.connect(IP_address,port)
    
        sock.sendall(b"ToggleOff")
    
        sock.close()
    except:
        print("exception occured trying to signal Unity")
    finally:
        return 0
try:
    # turn leds off
    gpio.output(Green_led_dynamic,gpio.LOW)
    gpio.output(Green_led_static,gpio.LOW)
    logstart = datetime.datetime.now()
    logFileName = CreateLogFileName(logstart)
    log = open(logFileName,"w")
    print(f"Running Trials at {logstart}")
    confirm = False
    while not confirm:
        response = input("Please confirm Saccade Rod is removed from the Robot (Y/N)")
        log.write(f"Comfirmed Saccade Rod Removed {response}\n")
        if(response.startswith("y") or response.startswith("Y")):
            confirm = True
        else:
           print("Invalid response please enter (Y/N) after removing the saccada rod from the Robot")
           log.write("Invalid response recieved ask again\n")
    
    while cycle== True:
        log.write("Home Axis\n")
        log.write('X axis move to start posn\n')
        
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
        my_file_list = []
        for file in os.listdir(Input_File_Path): # probably a bug here
            if file.endswith(".txt"):
               full_path = os.path.join(Input_File_Path, file) 
               my_file_list.append(full_path)
               log.write(f"Adding file {file} to list of files for trial\n")
               
        log.flush()
        os.fsync(log)
        current = target_position(500,500,1100) # debug code don't 
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
                        
                        if rowNumber == 0:
                            dateTime = datetime.datetime.now()
                            DataFileName = CreateDataFileName(dateTime, expCode, partCode)
                            BackupFileName = CreateBackupFileName(dateTime, expCode, partCode)
                            datafile = CreateDataFile(DataFileName)
                            
                        x_position = math.floor(float(dynamicX)*x_max) # wrong way for 0.4 -- went left, should have been right
                        y_position = math.floor(float(dynamicY)*y_max)
                        z_position = math.floor(float(dynamicZ)*z_max) # correct way for 0.6 -- went back
                        
                        log.write(f" Position is X = {current.X} Y= {current.Y} = {current.Z}\n")
                        #wait_time = int(row[7])/1000
                        nextposition2 = target_position(x_position,y_position,z_position)
                        move_to_position(current,nextposition2,0.001)
                        current=nextposition2
                        #def Led_Squencer(blink : int, dwell : int, gap : int, current_position : target_position
                        log.write(f"blink: {blink} dwell: {dwell} gap {gap}\n")
                        #Signal_Unity_On()
                        #blink : int, dwell : int, gap : int, static_position : target_position, current_position : target_position, datafile,log,experimentCode,trial,block,participant,visualangle,viewingDistance
                        Led_Sequencer(blink,dwell,gap,staticPosition, current, datafile, log, expCode, trialNum, blockNum, partCode, visualAngle, viewingDistance)
                        #Signal_Unity_Off()
                        sleep(0.2)
                        rowNumber+=1
                        print(f"Row: {rowNumber}") # debug code can be removed
                        
                    else: #
                        datafile.close()
                        shutil.copy(DataFileName,BackupFileName)
                
                
                inputfilename = CreateInputFileName(Input_File_Path,file)
                outputfilename = CreateOutputFileName(Output_File_Path,file)
                shutil.move(inputfilename,outputfilename) # did not work fix applied but not tested
                log.flush()
                os.fsync(log)

                
                #ToDo: prompt to continue here
                print("Block complete ")
                if Current_Block_Number == 3 and current_file_number ==3:
                    res3 = False
                    while res3 == False:
                        response3 = input("Please re-position the saccade rod and enter (Y/N) to continue or (Q) to exit the experiment")
                        log.write(f"Respone at block end {Current_Block_Number} file number {current_file_number} is {response3}\n")
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
        
except KeyboardInterrupt:
    log.write("Keyboard interrupt occured\n")
    log.close()
    gpio.cleanup()