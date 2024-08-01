#import numpy as np
#import pandas as pd
import csv

class Saccade_Instruction:
    trailNum   = -1
    staticX    = -1.999
    staticY    = -1.999
    staticZ    = -1.999
    dynamicX   = -1.999
    dynamicY   = -1.999
    dynamicZ   = -1.999
    dynamicCol = ""
    staticCol  = ""
    blink      = 0
    dwell      = -0.1
    gap        = 0
    
    def __init__(self, csv_row):
        parse_csv(csv_row)
        
    def parse_csv(csv_row):
        self.trialNum = int(csv_row[0])
        self.staticX = float(csv_row[1])
        self.staticY = float(csv_row[2])
        self.staticZ = float(csv_row[3])
        self.dynamicX = float(csv_row[4])
        self.dynamicY = float(csv_row[5])
        self.dynamicZ = float(csv_row[6])
        self.staticCol = csv_row[7]
        self.dynamicCol = csv_row[8]
        self.blink = float(csv.row[9])
        self.dwell = float(csv_row[10])
        self.gap = float(csv_row[11])


with open(fileName) as file:
    heading = next(file)
    reader = csv.reader(file)
    for row in reader:
        

txt_file = "square_movement.txt"

robot_instructions = pd.read_csv(txt_file)

print(robot_instructions)

# trial_num, start_x,y,z, end_x,y,z, dynamic_led, dynamic_col, static_led, static_col, blink_time, start_dwell, overlap, max_dwell