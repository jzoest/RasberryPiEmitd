
# direction const
CWDir = 0; // clockwise
CCWDir = 1; // Counter Clockwise
  
#float curX,curY,curZ;
curX=0.0
curY=0.0
curZ=0.0
#float tarX,tarY,tarZ;     // target xyz position
tarX=0.0
tarY=0.0
tarZ=0.0
#int tarA,tarB,posA,posB;  // target stepper position
tarA=0
tarB=0
posA=0
posB=0
#int8_t motorAfw,motorAbk; // Motor A forward or Motor A backwards
motorAfw=0
motorAbk=0
#int8_t motorBfw,motorBbk; // Motor B forward or Motor B backwards
motorBfw=0
motorBbk=0
stepTime=0.001

stepAuxDelay=0
stepdelay_min=1
stepdelay_max=1000
SPEED_STEP 1

#define
WIDTH = 1150
#define HEIGHT 2280
HEIGHT = 2280
#define STEPS_PER_MM 3 // the same as 3d printer
STEPS_PER_MM = 3

#int constrain(int x, int a, int b)
def contrain(x:int, a:int, b:int):
    result = x
    if x < a:
        result = a
    elif x > b:
        result = b
    
    return result

def MAX(a:int, b:int):
    result = a
    if b > a:
        result = b
    return result

# *********** motor movements ************
def stepperMoveA(direction:int):
    if direction > 0:
        gpio.output(MotorADir, CWDir)
    else:
        gpio.output(MotorADir, CCWDIR)
    gpio.output(MotorAPulse, gpio.HIGH)
    sleep(stepTime)
    gpio.output(MotorAPulse, gpio.LOW)
    sleep(stepTime/2)

def stepperMoveB(direction:int):
    if direction > 0:
        gpio.output(MotorBDir, CWDir)
    else:
        gpio.output(MotorBDir, CCWDIR)
    gpio.output(MotorBPulse, gpio.HIGH)
    sleep(stepTime)
    gpio.output(MotorBPulse, gpio.LOW)
    sleep(stepTime/2)

def doMove():
    mDelay=stepdelay_max
    speedDiff = -SPEED_STEP
    #int dA,dB,maxD;
    dA=0
    db=0
    maxD=0
    #float stepA,stepB,cntA=0,cntB=0;
    stepA=0.0
    stepB=0.0
    cntA=0.0
    cntB=0.0
    
    d=0
    
    dA = tarA - posA
    dB = tarB - posB
    maxD = MAX(abs(dA), abs(dB))
    stepA = abs(dA)/maxD
    stepB = abs(dB)/MaxD
    i=0
    while (posA!=tarA) or (posB!=tarB):
        #move A
        if posA != tarA:
            cntA+=tarA #increment by number of steps
            if cntA >= 1:
                if dA > 0:
                    d=motorAfw
                else:
                    d=motorAbk
                if dA > 0:
                    posA+=1
                else:
                    posA-=1
                stepperMoveA(d)
                cntA-=1
        if posB != tarB:
            cntB+=stepB
            if cntB >= 1:
                if dB > 0: # work out direction
                    d=motorBfw
                else:
                    d=motorBbk
                if dB > 0:
                    posB+=1
                else:
                    posB-=1
                stepperMoveB(d) # make one motor step B
                cntB-=1
        mDelay = contrain(mDelay+speedDiff,stepdelay_min,stepdelay+max)
        sleep(float(mDelay)/1000.0)
        if (maxD-i) < ((stepdelay_max-stepdelay_min)/SPEED_STEP):
            speedDiff=SPEED_STEP
        i+=1

def prepareMove():
    dx = float(tarX) - float(curX) # distance between target and current position
    dy = float(tarY) - float(curY) # distance between target and current position
    distance  = math.hypot(dx,dy) #calc hypotenus 
    if distance > 0.001:
        tarA = float(tarX)*STEPS_PER_MM
        tarB = float(tarY)*STEPS_PER_MM
        doMove()
        curX = tarX
        curY = tarY
