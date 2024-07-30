import datetime
import time

# datetime
current_time = datetime.datetime.now()
utc_time = datetime.utcnow()

# time
epochtime = int(time.time())

# final array,interleave Led_Data and Robot_Data with each other so that datetimes are in order
class Led_Data:
    datetime = 0
    led_state = "NULL"
    led_pin = -1
    
    def __init__(self, datetime, led_state, led_pin):
        self.datetime
        self.led_state = led_state
        self.led_pin = led_pin

led_arr = []

led_arr[0] = Led_Data(datetime.utcnow(), "HIGH", 21)

class Robot_Data:
    prev_datetime = 0
    prev_motor_a_steps = 0
    prev_motor_b_steps = 0
    prev_motor_y_steps = 0
    curr_datetime = 0
    curr_motor_a_steps = -1
    curr_motor_b_steps = -1
    curr_motor_y_steps = -1
    
    def __inti__(self, datetime, led_state, motor_a_steps, motor_b_steps, motor_y_steps):
        # set initial timestamp and motor steps
        self.datetime = datetime
        self.prev_motor_a_steps = motor_a_steps
        self.prev_motor_b_steps = motor_b_steps
        self.prev_motor_y_steps = motor_y_steps
    
    def update(datetime, motor_a_steps, motor_b_steps, motor_y_steps)
        curr_datetime = datetime
        curr_motor_a_steps = motor_a_steps
        curr_motor_b_steps = motor_b_steps
        curr_motor_y_steps = motor_y_steps
        
    def convert_corexz(motor_a_steps, motor_b_steps):
        # blah blah blah
    
    def convert_y_steps(motor_y_steps, y_steps_per_mm):
        y_axis_mm = motor_y_steps / y_steps_per_mm

#example code
        