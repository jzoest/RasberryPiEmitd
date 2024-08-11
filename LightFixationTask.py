import time
from time import sleep
import datetime
import os
import RPi.GPIO as gpio
import random

# Declare global variables.
Red_led_static = 16
Green_led_static = 24
Blue_led_static = 25

# GPIO set up for leds.
gpio.setmode(gpio.BCM)
gpio.setwarnings(False)
gpio.setup(Red_led_static, gpio.OUT)
gpio.setup(Green_led_static, gpio.OUT)
gpio.setup(Blue_led_static, gpio.OUT)

# setting directories and folder paths
Current_dir = "/home/emitd/src/python/RasberryPiEmitd"
os.chdir(Current_dir)
Data_File_Path   = os.path.join(Current_dir, "data_files")

# functions defined here
def CreateDataFileName(x: datetime, particpant):
    year  = x.year
    month = x.month
    day   = x.day
    hr    = x.hour
    mins  = x.minute
    sec   = x.second
    result = f"{Data_File_Path}//LightData_{year}{month}{day}T{hr}{mins}{sec}_{particpant}.csv"
    return result
    
def ValidateParticipantCode():
    response = False
    while response == False:
       participant_code = input("Please enter participant code (P##):")
       if len(participant_code) == 3:
           if participant_code[0] == "P":
               participant_number = participant_code[1] + participant_code[2]
               if participant_number.isnumeric():
                   if int(participant_number) > 0:
                       start_experiment = input("Valid participant code, please ensure participant is 60cm away from static LED target. Press Y to continue or Q to quit:")
                       if start_experiment == "Y" or start_experiment == "y":
                           response = True
                       elif start_experiment == "Q" or start_experiment == "q":
                           exit()
                   else:
                       print("Invalid participant code, please ensure code is greater than zero.")
               else:
                   print("Invalid participant code, last two characters are non-numeric.")
           else:
               print("Invalid participant code, please ensure code begins with uppercase P.")
       else:
           print("Invalid participant code length, please ensure code is only 3 characters.")
    
    return participant_code  

def RandomiseColour(led_array,randomInt, dwell):
    if led_array[0] == randomInt:
        gpio.output(Red_led_static, 1)
        sleep(dwell)
        gpio.output(Red_led_static, 0)
    elif led_array[1] == randomInt:
        gpio.output(Red_led_static, 1)
        gpio.output(Green_led_static, 1)
        sleep(dwell)
        gpio.output(Red_led_static, 0)
        gpio.output(Green_led_static, 0)
    elif led_array[2] == randomInt:
        gpio.output(Green_led_static, 1)
        sleep(dwell)
        gpio.output(Green_led_static, 0)
    elif led_array[3] == randomInt:
        gpio.output(Green_led_static, 1)
        gpio.output(Blue_led_static, 1)
        sleep(dwell)
        gpio.output(Green_led_static, 0)
        gpio.output(Blue_led_static, 0)
    elif led_array[4] == randomInt:
        gpio.output(Blue_led_static, 1)
        sleep(dwell)
        gpio.output(Blue_led_static, 0)
    elif led_array[5] == randomInt:
        gpio.output(Red_led_static, 1)
        gpio.output(Blue_led_static, 1)
        sleep(dwell)
        gpio.output(Red_led_static, 0)
        gpio.output(Blue_led_static, 0)
           
def StartTrial(participant, led_combination, trialDuration, totalTrialTime):
    
    # create file name
    current_datetime = datetime.datetime.now()
    dataFileName = CreateDataFileName(current_datetime, participant)

    # create file header
    header = "participant_code,start_timestamp,end_timestamp,\n"
    datafile = open(dataFileName,"w")
    datafile.write(header)
    
    # initialise timestamp to output file
    start_timestamp = datetime.datetime.now()
    
    steps = int(totalTrialTime/trialDuration)
    # starttrials
    for trial in range(steps):
        randomColour = random.randint(1,6)
        RandomiseColour(led_combination,randomColour,1)

    # initialise timestamp to output file
    end_timestamp = datetime.datetime.now()
    data_string = f"{participant},{start_timestamp},{end_timestamp},\n"
    datafile.write(data_string)
    # close file
    datafile.write("end,,,")
    datafile.close()
    
# Run routine:
gpio.output(Red_led_static, 0)
gpio.output(Green_led_static, 0)
gpio.output(Blue_led_static, 0)

participant = ValidateParticipantCode()

# assign combos
# 1 red
# 2 yellow/green
# 3 green
# 4 cyan
# 5 blue
# 6 purple
led_combination = []
for num in range(1,7):
    led_combination.append(num)

trialDuration = 1
totalTime = 120
StartTrial(participant, led_combination, trialDuration, totalTime)
