#import numpy as np
#import pandas as pd
import csv

class Robot_Instruction:
    trailNum = -1
    startX   = -1.999
    startY   = -1.999
    startZ   = -1.999
    endX     = -1.999
    endY     = -1.999
    endZ     = -1.999
    dynamicLed = False
    dynamicCol = ""
    staticLed = False
    staticCol = ""
    blink = -0.1
    startDwell = -0.1
    overlap = -10
    endDwell = -0.1
    
    def __init__(self, csv_row):
        parse_csv(csv_row)
        
    def parse_csv(csv_row):
        self.trialNum = int(csv_row[0])
        self.startX = float(csv_row[1])
        self.startY = float(csv_row[2])
        self.startZ = float(csv_row[3])
        self.startX = float(csv_row[4])
        self.startY = float(csv_row[5])
        self.startZ = float(csv_row[6])
        if csv_row[7] == "T":
            self.dynamicLed = True
        else:
            self.dynamicLed = False
        self.dynamicCol = csv_row[8]
        if csv_row[9] == "F":
            self.staticLed = True
        else:
            self.staticLed = False
        self.staticCol = csv_row[10]
        self.blink = float(csv_row[11])
        self.startDwell = float(csv_row[12])
        self.overlap = float(csv_row[13])
        self.endDwell = float(csv_row[14])


with open(fileName) as file:
    heading = next(file)
    reader = csv.reader(file)
    for row in reader:
        

txt_file = "square_movement.txt"

robot_instructions = pd.read_csv(txt_file)

print(robot_instructions)

# trial_num, start_x,y,z, end_x,y,z, dynamic_led, dynamic_col, static_led, static_col, blink_time, start_dwell, overlap, max_dwell