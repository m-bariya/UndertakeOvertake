#include "mbed.h"
#include "rtos.h"
#include "MODSERIAL.h"
#include "Servo.h"
 
//Link to pc via bluesmirf
MODSERIAL smirf(USBTX, USBRX);
//Link to chassis
MODSERIAL board2Board(PTC4, PTC3);

DigitalOut led_green(LED_GREEN);

// Keeps track of the current state. Only main should
// be able to change this.
int state;
///STATES///
#define DRIVE    0
#define OBSTACLE 1
#define PENDING  2
#define PEEKING  3
#define OVERTAKE 4
#define MANUAL   5
#define RETURN_TO_LANE 6

//Each sonar can sweep 180deg, in steps of 12deg
//Maybe we should collect two readings for each angle (allow for speed computation)
//Since I dont think the sonars need to sweep that large a range, this might be the best choice
//Timer for use when reading sonar data
Timer sonarClock;
int midPoint = 5;
float sonarFrontData[10];
float sonarBackData[10];
float sonarFrontTime[10];
float sonarBackTime[10];

//The state in which the current front sonar 
//data was collected.
int dataState1;
//The state in which the current back sonar
//data was collected.
int dataState2;

//Pins for servos under each sonar sensor
Servo servoFront(PTA4);
Servo servoBack(PTA5);
//assuming 6V power. If 4.8V, use 0.54
//Servo moves at 60deg/0.16s (https://www.sparkfun.com/products/11965)//
const float waitRate = 0.48;

//Pins for sensors
//AnalogIn -> AD
//DigitalOut -> Rx (only if we want to trigger read)
DigitalOut sonarFrontTrigger(PTC12)
DigitalOut sonarBackTrigger(PTC13)
AnalogIn sonarFrontIn(PTB1)
AnalogIn sonarBackIn(PTB2)

//Values for calculating distance from sonar
/*IF CHANGED, PLEEZ SET CORRECTLY*/
const float sonarVcc = 5; 

// Number of sonar measurements made (state-dependent).
// Corresponds to the number of measurements made in a
// sweep in one direction.
int numDriveAngles = 1;
int numObstacleAngles = 1;
int numPendingAngles = 3;
int numPeekingAngles = 3;
int numOvertakeAngles = 1;
int numReturnAngles = 3;

//Front sonar angles (state dependent)
float driveAng1[numDriveAngles] = {0}
float obstacleAng1[numObstacleAngles] = {0}
float pendingAng1[numPendingAngles] = {0, 22.5, 45};
float peekingAng1[numPeekingAngles] = {0, 22.5, 45};
float overtakeAng1[numOvertakeAngles] = {0}
float returnToLaneAng1[numReturnAngles] = {0, -22.5, 45}

//Back sonar angles (state dependent)
float peekingAng2[numPeekingAngles] = {} //TODO
float overtakeAng2[numOvertakeAngles] = {0}; 
float returnToLaneAng2[numReturnAngles] = {0, -22.5, 45};

//CONSTANTS NEEDED IN EACH STATE//
//organized by state for clarity//

//DRIVE
//default speed = 0.6 m/s//
float fixedSpeed = 0.6;
//OBSTACLE



///////////////SERVO+SONAR/////////////////////////////////////////////////

//Set angle of servo (1=front, 2=back)
void setServoAngle(int servo, float angleIn) {
    float angle = servoDegToPos(angleIn);
    float currAngle;
    float delTime;
    if(servo==1){

        currAngle = servoFront;

        if (currAngle==angle) {
            return;
        }

        delTime = abs(currAngle-angle)*waitRate;
        servoFront = angle;
        Thread::wait(delTime);

    } else {

        currAngle = servoBack;

        if (currAngle==angle){
            return;
        }

        delTime = abs(currAngle-angle)*waitRate;
        servoBack = angle;
        Thread::wait(delTime);

    }
}

/*'Efficiently sweeps sonar over an angle range (twice, back & forth) 
and updates values in corressponding array*/
void sweepServoAngle(int servo, float *angleList) {
    int N = sizeof(angleList)/sizeof(angleList[0]);
    float reading;

    /*Forward sweep through angles*/
    int i = 0;
    sonarTimer.start();
    for (i = 0; i < N; i++) {
        currAngle = angleList[i];
        setServoAngle(servo, currAngle);
        reading = readSonar(servo);

        if (servo==1) {
            sonarFrontData[i] = reading;
        } else {
            sonarBackData[i] = reading;
        }
    }

    /*Reverse sweep through angles*/
    for (i = N-1; i >= 0; i++) {
        currAngle = angleList[i];
        setServoAngle(servo, currAngle);
        reading = readSonar(servo)

        if (servo==1) {
            sonarFrontData[midPoint+i] = reading;
        } else {
            sonarBackData[midPoint+i] = reading;
        }
    }
  sonarTimer.reset();
}

//Read distance value of sonar (1=front, 2=back)
float readSonar(int sonar) {
    float result;
    if(sonar==1) {
        sonarFrontTrigger = 1;
        Thread::wait(0.02);
        sonarFrontTrigger = 0;

        //read sonar value
        result = sonarFrontIn;
    }else{
        sonarBackTrigger = 1;
        Thread::wait(0.02);
        sonarBackTrigger = 0;

        //read sonar value
        result = sonarBackIn;
    }
    return sonarToDist(result);
}

/*Converts from an intuitive 'degrees' to the % values the
servo expects*/
float servoDegToPos(float degrees) {
    pos = (degrees / 180) + 0.5;
    return pos;
}

/*Converts sonar output to distance in cm*/
float sonarToDist(float reading) {
    // Formula to convert sensor reading into a distance value
    // see: http://www.maxbotix.com/articles/032.htm
    float distance = ((reading*1024) / sonarVcc)*5; 
    // Converting to cm here. Remove to keep in mm
    distance = distance / 10;
    return distance;
}

/**
 * Returns the speed of an obstacle.
 *
 * d1 -- distance measurement from first sweep [cm]
 * d2 -- distance measurement from second sweep [cm]
 * dT -- delta time value between distance measurements [ms]
 * currSpeed -- current speed of our car [m/s]
 */
float speedEstimate(float d1, float d2, float dT, float currSpeed) {
    // convert cm to m and ms to s
    d1 = d1 / 10;
    d2 = d2 / 10;
    dT = dt * 1e-3;
    // calculate speed estimate of object
    return (currSpeed - (abs(d2-d1)/dT));
}

/**
 * Controls front sonar (1). Responsible for both
 * controlling the sonar and storing its measured
 * values.
 */
void sonar1(void const *args) {
    //FRONT SONAR CONTROL
    while(1){
        switch(state) {
        case DRIVE:
            //only need to look straight ahead, checking for obstacle distance
            //**NOTE** on turns, straight ahead may not be adequate, so might have
            //to change this.
            sweepServoAngle(1, driveAng1);
            dataState1 = DRIVE;
            break;
        case OBSTACLE:
            //only need to look straight ahead, constantly checking obstacle distance
            sweepServoAngle(1, obstacleAng1);
            dataState1 = OBSTACLE;
            break;
        case PENDING:
            //look straight ahead for same lane car and check on left
            sweepServoAngle(1, pendingAng1);
            dataState1 = PENDING;
        case PEEKING:
            //look slightly left maybe from 0 to 30 where 0 is straight
            sweepServoAngle(1, peekingAng1);
            dataState1 = PEEKING;
            break;
        case OVERTAKE:
            // look straight ahead
            sweepServoAngle(1, overtakeAng1);
            dataState1 = OVERTAKE;
            break;
        case MANUAL:
            //nothing
            break;
        case RETURN_TO_LANE:
            // for simple case, dont need FRONT. 
            // but if we add an abort case, then will need front
            sweepServoAngle(1, returnToLaneAng1);
            dataState1 = RETURN_TO_LANE;
            break;
        }
        //wait 0.5 seconds
        Thread::wait(500);
    }
}

/**
 * Controls back sonar (2). Responsible for both
 * controlling the sonar and storing its measured
 * values.
 */
void sonar2(void const *args) {
    switch(state) {
        case DRIVE:
            //DON'T CARE: don't need back sonar during drive
            break;
        case OBSTACLE:
            //DON'T CARE: don't need back sonar during obstacle following
            break;
        case PENDING:
            //DON'T CARE: don't need back sonar during pending.
            break;
        case PEEKING:
            //check right flank in case we want to check whether return to lane 
            //after peeking is safe
            sweepServoAngle(2, peekingAng2);
            dataState2 = PEEKING;
            break;
        case OVERTAKE:
            // look straight ahead
            sweepServoAngle(2, overtakeAng2);
            dataState2 = OVERTAKE;
            break;
        case MANUAL:
            //nothing
            break;
        case RETURN_TO_LANE:
            // check left to see if safe to return to lane
            sweepServoAngle(2, returnToLaneAng2);
            dataState2 = RETURN_TO_LANE;
            break;
        }

        Thread::wait(100);
    }
}

/////////////////////////////////////////////////////////////////////////////////

float behindObstacle() {
    float threshold = 100; //100 cm = 1m
}

// Updates what the current state should be
int main(void) {
    // Main has initial thread priority normal
    /////////////// Initialize threads //////////////////
    Thread thread(sonar1);
    Thread thread(sonar2);
  
    while(1) {
        switch(state) {
        case DRIVE:
            //Drive at a constant speed
            sendToChassis(0, 0, fixedSpeed);

            if (behindObstacle()) {
                state = OBSTACLE;
            }
            break;
        case OBSTACLE:
            if (overtakeToggle) {
                state = PENDING;
            }
            //Use distance to object in same lane 
            //to determine speed (some control required)
            float speed = sonar1Dist;
            comms("CH,0,0,%f", speed);
            break;
        case PENDING:
            // Same action as OBSTACLE
            float speed = sonar1Dist;
            comms("CH,0,0,%f", speed);
            break;
        /**
         * PEEKING:
         *
         * The sonar values will be provided as cm measurements.
         * Assuming the test cars move at 0.5m/s, and it takes XXX sec
         * to successfully overtake, the threshold should be set to
         * XXX cm.
         * NOTE/TODO: Do we need to add any angle information here, 
         * because angle of sonar affects distance reading.
         */
        case PEEKING:
            int i, overtakeTime = 2000;
            // Distances in cm
            float minVal1 = 1000, minVal2 = 1000, threshold = 100;
            // Speeds in m/s
            float obstacleSpeed, obstacleDistance;
            // Get minimum distances from both forward and backward sweeps.
            // Forward sweep (l->r)
            for (i = 0; i < numPeekingAngles; i = i + 1) {
                if (sonarFrontData1[i] < minVal1) {
                    minVal1 = sonarFrontData[i];
                }
            }
            // Backward sweep (r->l)
            for (i = midpoint; i < midpoint + 2; i = i + 1) {
                if (sonarFrontData[i] < minval2) {
                    minVal2 = sonarFrontData[i];
                }
            }
            if ((minVal1 > treshold) && (minVal2 > threshold)) {
                obstacleSpeed = speedEstimate(minVal1, minVal2, peekTime, fixedSpeed);
                obstacleDistance = fminf(minVal1, minVal2) - (obstacleSpeed*overtakeTime)
                if (obstacleDistance > threshold || obstacleDistance < 0) {
                    state = OVERTAKE;
                }
            }
            break;
        case OVERTAKE:
            break;
        case MANUAL:
            char inputCmd = readFromBluesmirf()
            writeToDriver(inputCmd)
            break;
        case RETURN_TO_LANE:
            break;
    }
        // Wait for 150 ms (0.15s)
        Thread::wait(150);
    }
}

//For safekeeping, basically need a function that sends a string to chassis
void comms(char inputStr[30]) {
    char inputStr[30];
    char outputStr[30];
    char *token;

    smirf.printf("enter input command: DR,<float>,<int>,<int>,<int>\n");
    led_green = 1;
    while(1)
    {
        float floatVal;
        int intVal;
        int boolVal1, boolVal2;

        if (smirf.readable()) { 
            //Get input characters until '\r'
            char curr= ' ';
            int idx = 0;
            while (curr != '\r') {
                curr = smirf.getc();
                inputStr[idx] = curr;
                idx = idx + 1;
            }
            //fyi: print the received string back to the smirf
            smirf.printf("recv: %s", inputStr);

            token = strtok(inputStr, ",");
            if (strcmp(token,"DR")==0) {
                led_green = 0;
                char * pEnd;
                floatVal = strtof(strtok(NULL, ","), &pEnd);
                intVal = strtol(strtok(NULL, ","), &pEnd, 10);
                boolVal1 = strtol(strtok(NULL, ","), &pEnd, 10);
                boolVal2 = strtol(strtok(NULL, ","), &pEnd, 10);
                
                sprintf(outputStr, "CH,%2.3f,%d,%d,%d\r\n",floatVal,intVal, boolVal1, boolVal2); // fyi
                smirf.printf("%s", outputStr); //fyi
            }
          
            

            // Send an output to the chassis unit in the form:
            // CH, <int>, <bool>, <float>, \r\n

            //Need to do some computation/thought to determine these actual
            //values. **Placeholder**
            int prefLane = 0;
            int peek = 0;
            float speed = 3.0;

            sprintf(outputStr, "CH,%d,%d,%2.3f,\r\n",prefLane,peek,speed);
        } else {
            // If no command, print heartbeat
            strcpy(outputStr, "HB,\r\n");
        }
      
        
        
        board2Board.printf("%s", outputStr);
}

sendToChassis(int lane, int peek, float speed) {
    char outputStr[30];
    sprintf(outputStr, "CH,%d,%d,%2.3f,\r\n",prefLane,peek,speed);
    board2Board.printf("%s", outputStr);
}

sendToPC(char *inputStr) {
    sprintf(inputStr);
}

//add a function which reads from bluetooth and board2Board