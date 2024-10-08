from optparse import check_builtin
import mesa
import random
import math

""" Extended Features from Assignment 2 """
NEW_DEBRIS_CHANCE = 0.01     # Chance to add new debris to beach 
VOTING_TYPE = "PLURALITY"    # PLURALITY or ANTIPLURALITY

""" Novel Feature Parameters"""
n_clusters = 6                # Number of clusters of debris
cluster_spread = 3            # Max distance of debris from cluster
pheromone_strength = 200       # Base pheromone strength, decreases by 1 each timestep

""" Beach Parameters"""
NUMBER_OF_CELLS = 75
n = 0
n_segments = 10              # Must be large otherwise agents may miss areas/debris
CT_explored_segments = []    # Makes it more likely that unexplored segments will be targeted
LC_explored_segments = []

""" Agent States """
IDLE = 0              # Idle (Default State)
EXPLORING = 1         # Exploring in random direction and magnitude
EMPTYING = 2          # Moving towards wastebin / Emptying cargo
CHARGING = 3          # Moving towards charging point/ Waiting to be fully charged
PICKING = 4           # Moving to target
FOLLOWING_TRAIL = 5   # LC agent following pheromone trail

""" Debris States """
UNDONE = 0
UNDERWAY = 2
DONE = 1

""" Agent Parameters """
# General Parameters
SCAN_RANGE = 5

# CT Parameters
CT_MAX_PAYLOAD = 3
CT_SPEED = 1
NEEDS_CHARGE = True
MAX_CHARGE = 750     # Maximum starting charge
MIN_CHARGE = 100     # Reserve charge when determining when to returning to charging station 
CHARGING_SPEED = 50  # Charge restored each step once at charging station

# LC Parameters
LC_MAX_PAYLOAD = 10
LC_SPEED = 3


class CT_Robot(mesa.Agent):
    """Represents a CT Robot on the beach."""
    def __init__(self, id, pos, model, max_payload=CT_MAX_PAYLOAD, speed=CT_SPEED, init_state=IDLE):
        super().__init__(id, model)
        self.x, self.y = pos
        self.next_x, self.next_y = None, None
        self.state = init_state
        self.payload = []
        self.max_payload = max_payload
        self.speed = speed
        self.target = None # (x,y,unique_id)
        self.reserve_target = None # Used to reserve target incase agent must return to charging station
        self.reserve_state = None
        self.charge = random.randint(MAX_CHARGE/2, MAX_CHARGE) # CTs start with 50% to 100% charge
        self.chp_distance = self.get_chp_distance()            # Keeps track of distance to charging point
        self.charge_spent = 0
        self.total_collected = 0

    @property
    def isBusy(self):
        return (self.state==EXPLORING or self.state == PICKING)
  
    @property
    def atChargingPoint(self):
        chp = [a for a in self.model.schedule.agents if isinstance(a,ChargingPoint)]
        return (self.x == chp[0].x and self.y == chp[0].y)
    
    @property
    def atWasteBin(self):
        wb = [a for a in self.model.schedule.agents if isinstance(a,WasteBin)]
        return self.x == wb[0].x and self.y == wb[0]
    
    @property
    def must_return(self):
        return self.chp_distance + MIN_CHARGE >= self.charge

    
    def targetChargingPoint(self):
        chp = [a for a in self.model.schedule.agents if isinstance(a,ChargingPoint)]
        self.target = (chp[0].x, chp[0].y, chp[0].unique_id)

    def targetWasteBin(self):
        wb = [a for a in self.model.schedule.agents if isinstance(a,WasteBin)]
        self.target = (wb[0].x, wb[0].y, wb[0].unique_id)
        print("Wastebin is at:", wb[0].x, wb[0].y)

    def LargeDebrisLeft(self):
        ld = [a for a in self.model.schedule.agents if (isinstance(a,LargeDebris) and (a.state == UNDONE or self.state == UNDERWAY))]
        return len(ld) != 0
    
    def hold_target(self):
        print("Holding Target")
        assert self.reserve_target == None
        self.reserve_target = self.target
        self.target = None
        self.reserve_state = self.state

    def resume(self):
        """
        Continues reserve target and state if any
        """
        print("Resuming Previous task if any")
        if self.reserve_target:
            self.target = self.reserve_target
            self.reserve_target = None
            print("target is now at", self.target[0], self.target[1])

            self.state = self.reserve_state
            self.reserve_state = None
            print("state is now", self.state)
        else:
            self.state = IDLE
            self.target = None
            self.reserve_state = None
            self.reserve_target = None
    

    def step(self):
        """
        * Obtain action as a result of deliberation
        * trigger action
        """
        action = getattr(self, self.deliberate())
        action()

    # Robot decision model
    def deliberate(self):
        """
        Simple rule-based architecture, should determine the action to execute based on the robot state.
        """

        # Debug Print Statements 
        """
        print("CT", self.unique_id, "state is:", self.state)
        print("CT", self.unique_id, "position is: ", self.x, ",", self.y)
        if self.target:
            print("CT", self.unique_id, "target is at:", self.target[0], self.target[1])
        print("CT", self.unique_id, "payload is:", len(self.payload))
        print("Payload contains", self.payload)
        print("CT", self.unique_id, "charge is:", self.charge)
        print("Distance to charging station is:", self.chp_distance)
        print("Must return", self.must_return)
        """

        ld  = [a for a in self.model.schedule.agents if (isinstance(a,LargeDebris) and (a.state == UNDONE or self.state == UNDERWAY))]
        print("Large Debris left", len(ld))
        d  = [a for a in self.model.schedule.agents if (isinstance(a,Debris) and (a.state == UNDONE or self.state == UNDERWAY))]
        print("Debris left", len(d))

        # Assertions
        assert(self.charge >= 0)

        # Default action (End)
        action = "wait"

        # Check if CT needs to return to charging station
        if self.must_return:
                print("CT returning to charging station")
                if self.state == PICKING:
                    self.hold_target()                    
                self.state = CHARGING

        # Continue with previous target if current target is finished
        if not self.target and self.reserve_target:
                print("Continuing with target")
                self.resume()


        if self.state == EXPLORING:
            if not self.target:
                self.set_explore_target()
            elif self.x == self.target[0] and self.y == self.target[1]:
                self.set_explore_target()

            if self.find_target(): # Target within range
                self.state = PICKING
            else:
                action = "move_fw"

        elif self.state == CHARGING:
            if self.charge >= MAX_CHARGE:
                self.state = IDLE
                self.charge = MAX_CHARGE
                self.target = None
            
            elif self.atChargingPoint:
                print("CT is at chargingpoint, now waiting until fully charged")
                self.charge += CHARGING_SPEED
                print("charge is now",self.charge)
                action = "wait"
            else:
                print("moving towards charging point")
                self.targetChargingPoint()
                action = "move_fw"


        elif self.state == EMPTYING:
            if (self.x == self.target[0] and self.y == self.target[1]):
                print("CT is at wastebin, now unloading")
                action = "drop_off"
            else:
                print("moving towards waste bin")
                action = "move_fw"


        elif self.state == IDLE:
            # If all LargeDebris are done
            if not self.LargeDebrisLeft() and self.payload:
                print("there are no LargeDebris left to do")
                print("Moving Payload to waste bin")
                action = "move_to_bin"
                self.state = EMPTYING
                return action
            
            elif not self.LargeDebrisLeft():
                print("there are no LargeDebris left to do")
                self.state = CHARGING
                action = "goto_charging_station"
                return action
            
            elif len(self.payload) >= self.max_payload:
                print("moving to bin")
                action = "move_to_bin"

            elif self.LargeDebrisLeft():
                print("Robot is now exploring")
                self.state = EXPLORING

            else:
                return action


        elif self.state == PICKING:
            if (self.x == self.target[0]) and (self.y == self.target[1]):
                print("Robot is now picking debris up")
                action = "pick"
            else:
                print("Robot is now moving forwards")
                action = "move_fw"

        else:
            print("Robot is now returning to charging station")
            action = "goto_charging_station"
        return action

    # Robot actions
    def set_explore_target(self):
        """
        * Splits map into segments and sets the target to random segment centre
        * Keeps track of explored segments so they are not explored again
        """
        while True:
            x_segment = random.randint(1, n_segments)
            y_segment = random.randint(1, n_segments)

            x = math.floor(x_segment*NUMBER_OF_CELLS/(n_segments))-1
            y = math.floor(y_segment*NUMBER_OF_CELLS/(n_segments))-1

            if self.containsObstacle(x,y):
                #print("cell contains obstacle, finding new one")
                continue
            if (x,y) in CT_explored_segments:
                # if more than 90% of segments have been explored, reset explored segments
                if len(CT_explored_segments) > 0.9* n_segments**2:
                    CT_explored_segments.clear()
                #print("CT segment already explored")
                continue

            print("Exploring around cell", x, y)
            CT_explored_segments.append((x,y))
            self.target = (x, y)
            break

    def find_target(self):
        """
        Finds Large Debris within area and sets it as target.
        If no Large Debris found, continue exploring.
        """
        debris = [a for a in self.model.schedule.agents if (isinstance(a,LargeDebris) and (a.unique_id not in self.payload) and a.state == UNDONE)]

        if debris == []:
            #print("No Target Found")
            self.state = IDLE
            return False

        # Get closes Large Debris
        closest_debris = debris[0]
        for ld in debris:
            if get_distance(self, ld) < get_distance(self, closest_debris):
                closest_debris = ld

        if get_distance(self, closest_debris) <= SCAN_RANGE:
            closest_debris.state = UNDERWAY
            self.target = (closest_debris.x, closest_debris.y, closest_debris.unique_id)
            self.state = PICKING
            return True
        else:
            return False


    def move_to_bin(self):
        bin = [a for a in self.model.schedule.agents if isinstance(a,WasteBin)]
        self.state = EMPTYING
        self.target = (bin[0].x, bin[0].y, bin[0].unique_id)

    def goto_charging_station(self):
        chp = [a for a in self.model.schedule.agents if isinstance(a,ChargingPoint)]
        if self.target and self.state == PICKING:
            self.hold_target()
        self.state = CHARGING
        self.target = (chp[0].x,chp[0].y, chp[0].unique_id)


    def move(self):
        """
        Move robot to the next position.
        """
        cells_moved = abs(self.x - self.next_x) + abs(self.y - self.next_y)

        self.model.grid.move_agent(self, (self.next_x, self.next_y))
        self.x = self.next_x
        self.y = self.next_y

        if NEEDS_CHARGE:
            self.charge -= cells_moved
            self.charge_spent += cells_moved

        # Update recorded distance to charging point
        self.chp_distance = self.get_chp_distance()


    def move_payload(self):
        """
        * Obtains the Large Debris whose id is in the payload
        * move the payload together with the robot
        """
        debris = [a for a in self.model.schedule.agents if isinstance(a,LargeDebris) and a.unique_id in self.payload]
        for ld in debris:
            self.model.grid.move_agent(ld,(self.x,self.y))


    def wait(self):
        """
        Keep the same position as the current one.
        """
        self.next_x = self.x
        self.next_y = self.y


    def move_fw(self):
        """Move the robot towards the target"""
        x_dif = abs(self.x - self.target[0])
        y_dif = abs(self.y - self.target[1])

        if x_dif == 0 and y_dif == 0:
            self.state = IDLE

        if (x_dif > self.speed) and (self.target[0] > self.x):
            self.next_x = self.x + self.speed
        elif (x_dif > self.speed) and (self.target[0] < self.x):
            self.next_x = self.x - self.speed
        else:
            self.next_x = self.target[0]

        if (y_dif > self.speed) and (self.target[1] > self.y):
            self.next_y = self.y + self.speed
        elif (y_dif > self.speed) and (self.target[1] < self.y):
            self.next_y = self.y - self.speed
        else:
            self.next_y = self.target[1]

        # Obstacle avoidance using random movement
        if self.containsObstacle(self.next_x,self.next_y):
            print("next tile has an obstacle, changing next tile")
            
            while True:
                move = random.choice(["up","down","left","right"])
                if move == "up":
                    if self.containsObstacle(self.x,self.y+1) or self.y == NUMBER_OF_CELLS:
                        continue
                    self.next_y = self.y+1
                    break

                if move == "down":
                    if self.containsObstacle(self.x,self.y-1) or self.y == 0:
                        continue
                    self.next_y = self.y-1
                    break

                if move == "left":
                    if self.containsObstacle(self.x-1,self.y)or self.x == 0:
                        continue
                    self.next_x = self.x-1
                    break

                if move == "right":
                    if self.containsObstacle(self.x+1,self.y)or self.x == NUMBER_OF_CELLS:
                        continue
                    self.next_x = self.x+1
                    break

        self.move()
        self.move_payload()

        
    def pick(self):
        """
        * find out the id of the Large Debris next to the robot
        * store the Large Debris id in the payload of the robot
        * set state to EMPTYING if max payload is met or IDLE
        """
        debris = [a for a in self.model.schedule.agents if isinstance(a,LargeDebris) and a.unique_id==self.target[2]]
        debris[0].state = UNDERWAY
        self.payload.append(self.target[2])
        print("Payload is now", self.payload)

        self.total_collected += 1

        # If maximum payload is exceeded set target to waste bin
        if len(self.payload) >= self.max_payload:
            self.state = EMPTYING
            wb = [a for a in self.model.schedule.agents if isinstance(a,WasteBin)]
            self.target = (wb[0].x, wb[0].y, wb[0].unique_id)
            print("Heading towards waste bin at", self.target[0], self.target[1])
        else:
            self.target = None
            self.resume()
    
    def drop_off(self):
        """
        * change state of the robot to IDLE
        * Get the Large Debris whose id is in the payload and remove it from the grid and change its state to Done.
        * Remove payload from robot
        """
        self.state = IDLE
        debris = [a for a in self.model.schedule.agents if isinstance(a,LargeDebris) and a.unique_id in self.payload]
        
        print("Removing Debris/s from game")
        for ld in debris:
            ld.state = DONE
            self.model.grid.remove_agent(ld)
        
        self.payload = []
        self.target = None
        self.move()
   
    def advance(self):
       """
       Advances position of the robot.
       """
       self.x = self.next_x
       self.y = self.next_y
    
    def containsObstacle(self, x,y):
        obstacles = [a for a in self.model.schedule.agents if isinstance(a,Obstacle) and a.x == x and a.y == y]
        if obstacles:
            return True
        else: 
            return False
        
    def get_chp_distance(self):
        chp = [a for a in self.model.schedule.agents if isinstance(a,ChargingPoint)]
        return get_distance(self, chp[0])
        
    
class LC_Robot(mesa.Agent):
    """Represents a LC Robot on the beach."""
    def __init__(self, id, pos, model, max_payload=LC_MAX_PAYLOAD, speed=LC_SPEED, init_state=IDLE):
        super().__init__(id, model)
        self.x, self.y = pos
        self.next_x, self.next_y = None, None
        self.state = init_state
        self.payload = 0
        self.max_payload = max_payload
        self.speed = speed
        self.target = None       # (x,y,unique_id)
        self.next_ph = None      # To setup trail of pheromones
        self.trail_cooldown = 0  # Allows agent to explore at end of trail
        self.last_placed = None


    @property
    def isBusy(self):
        return (self.state==EXPLORING or self.state == PICKING)
    
    @property
    def atWasteBin(self):
        wb = [a for a in self.model.schedule.agents if isinstance(a,WasteBin)]
        return self.x == wb[0].x and self.y == wb[0]

    @property
    def LargeDebris_within_range(self):
        ld = [a for a in self.model.schedule.agents if isinstance(a,LargeDebris) and get_distance(self, a) < SCAN_RANGE and a.state == UNDONE]
        if ld:
            return ld[0]

    @property
    def pheromones_within_range(self):
        ph = [a for a in self.model.schedule.agents if isinstance(a,Pheromone) and get_distance(self, a) < SCAN_RANGE]
        print("finding pheromones within range")
        if ph:
            print("Pheromone found")
            return ph
        else: 
            print("Pheromone not found")
            return False

    def targetWasteBin(self):
        wb = [a for a in self.model.schedule.agents if isinstance(a,WasteBin)]
        self.target = (wb[0].x, wb[0].y, wb[0].unique_id)

    def DebrisLeft(self):
        debris = [a for a in self.model.schedule.agents if (isinstance(a,Debris) and (a.state == UNDONE))]
        return len(debris) != 0
    
    def LargeDebrisLeft(self):
        ld = [a for a in self.model.schedule.agents if (isinstance(a,LargeDebris) and (a.state == UNDONE or self.state == UNDERWAY))]
        return len(ld) != 0


    def step(self):
        """
        * Obtain action as a result of deliberation
        * trigger action
        """
        if self.model.NOVEL:
            action = getattr(self, self.deliberate_ACO())
            self.trail_cooldown -= 1
            if self.trail_cooldown < 0:
                self.trail_cooldown = 0
        else:
            action = getattr(self, self.deliberate())

        action()


    def deliberate_ACO(self):
        """
        Simple rule-based architecture, should determine the action to execute based on the robot state.
        """
        # Debug Print Statements
        print("LC", self.unique_id, "state is:", self.state)
        print("LC", self.unique_id, "position is: ", self.x, ",", self.y)
        if self.target:
            print("LC", self.unique_id, "target is at:", self.target[0], self.target[1])
        print("Payload is", self.payload)

        # Default action (End)
        action = "wait"

        # Create Job if large debris found
        ld = self.LargeDebris_within_range
        if ld:
            self.create_job(ld)

        if self.state == FOLLOWING_TRAIL:
            # If debris in range pick it
            if self.find_target(): # Target within range
                self.state = PICKING

            elif (self.x == self.target[0] and self.y == self.target[1]):
                if self.next_ph.next_ph:
                    print("following trail")
                    self.target = (self.next_ph.next_ph.x, self.next_ph.next_ph.y, self.next_ph.next_ph.unique_id)
                    self.next_ph = self.next_ph.next_ph
                    print("new target is",self.target)
                    print("new next_ph is", self.next_ph)
                    action = "move_fw"
                else:
                    self.next_ph = None
                    self.target = None
                    self.state = EXPLORING
                    self.trail_cooldown += 10
            else:
                if self.containsObstacle(self.target[0], self.target[1]):
                    self.next_ph = None
                    self.target = None
                    self.state = EXPLORING
                    self.trail_cooldown += 10
                else:
                    action = "move_fw"


        elif self.state == EXPLORING:
            if not self.DebrisLeft() and not self.LargeDebrisLeft():
                self.state = IDLE
                return action

            if self.find_target(): # Debris within range
                self.state = PICKING
            
            elif self.pheromones_within_range and self.trail_cooldown == 0:
                print("detecting pheromones")
                self.state = FOLLOWING_TRAIL
                self.next_ph = self.choose_trail()
                self.target = [self.next_ph.x, self.next_ph.y,self.next_ph.unique_id]
                while self.containsObstacle(self.target[0], self.target[1]):
                    self.target = [self.next_ph.next_ph.x, self.next_ph.next_ph.y,self.next_ph.next_ph.unique_id]
                action = "move_fw"

            elif not self.target or self.x == self.target[0] and self.y == self.target[1]:
                self.set_explore_target()

            else:
                action = "move_fw"

        elif self.state == EMPTYING:
            if (self.x == self.target[0] and self.y == self.target[1]):
                print("CT is at wastebin, now unloading")
                action = "drop_off"
            else:
                #print("moving towards waste bin")
                self.place_pheromone()
                action = "move_fw"

        elif self.state == IDLE:
            # If no debris left
            if not self.DebrisLeft() and not self.LargeDebrisLeft():
                #print("there are no debris left to do")
                return action
            
            elif not self.DebrisLeft() and self.payload:
                #print("there are no debris left to do")
                #print("Moving Payload to waste bin")
                action = "move_to_bin"
                return action
            
            if self.payload >= self.max_payload:
                #print("moving to bin")
                action = "move_to_bin"

            elif self.DebrisLeft() or self.LargeDebrisLeft():
                if self.pheromones_within_range:
                    self.state = FOLLOWING_TRAIL
                    self.next_ph = self.choose_trail()
                    self.target = [self.next_ph.x, self.next_ph.y, self.next_ph.unique_id]

                else:
                    print("Robot is now exploring")
                    self.state = EXPLORING
            else:
                self.state = IDLE

        elif self.state == PICKING:
            if (self.x == self.target[0]) and (self.y == self.target[1]):
                #print("Robot is now picking")
                action = "pick"
            else:
                #print("Robot is now moving forwards")
                action = "move_fw"
        else:
            #print("Robot is now returning to charging station")
            action = "goto_charging_station" # Return to base
        return action

    
    # Robot decision model
    def deliberate(self):
        """
        Simple rule-based architecture, should determine the action to execute based on the robot state.
        """
        # Debug Print Statements
        #print("LC", self.unique_id, "state is:", self.state)
        #print("LC", self.unique_id, "position is: ", self.x, ",", self.y)
        #if self.target:
        #    print("LC", self.unique_id, "target is at:", self.target[0], self.target[1])
        #print("Payload is", self.payload)

        # Default action (End)
        action = "wait"

        # Create Job if large debris found
        ld = self.LargeDebris_within_range
        if ld:
            self.create_job(ld)

        if self.state == EXPLORING:
            if not self.DebrisLeft() and not self.LargeDebrisLeft():
                self.state = IDLE
                return action

            if not self.target or self.x == self.target[0] and self.y == self.target[1]:
                self.set_explore_target()

            if self.find_target(): # Target within range
                self.state = PICKING
            else:
                action = "move_fw"

        elif self.state == EMPTYING:
            if (self.x == self.target[0] and self.y == self.target[1]):
                print("CT is at wastebin, now unloading")
                action = "drop_off"
            else:
                #print("moving towards waste bin")
                action = "move_fw"

        elif self.state == IDLE:
            # If no debris left
            if not self.DebrisLeft() and not self.LargeDebrisLeft():
                #print("there are no debris left to do")
                return action
            
            elif not self.DebrisLeft() and self.payload:
                #print("there are no debris left to do")
                #print("Moving Payload to waste bin")
                action = "move_to_bin"
                return action
            
            if self.payload >= self.max_payload:
                #print("moving to bin")
                action = "move_to_bin"

            elif self.DebrisLeft() or self.LargeDebrisLeft():
                #print("Robot is now exploring")
                self.state = EXPLORING
            else:
                self.state = IDLE

        elif self.state == PICKING:
            if (self.x == self.target[0]) and (self.y == self.target[1]):
                #print("Robot is now picking")
                action = "pick"
            else:
                #print("Robot is now moving forwards")
                action = "move_fw"
        else:
            #print("Robot is now returning to charging station")
            action = "goto_charging_station" # Return to base
        return action

    
    # Robot actions
    def set_explore_target(self):
        """
        * Splits map into segments and sets the target to random segment centre
        """
        while True:
            x_segment = random.randint(1, n_segments)
            y_segment = random.randint(1, n_segments)

            x = math.floor(x_segment*NUMBER_OF_CELLS/(n_segments))-1
            y = math.floor(y_segment*NUMBER_OF_CELLS/(n_segments))-1

            if self.containsObstacle(x,y):
                #print("cell contains obstacle, finding new one")
                continue
            if (x,y) in LC_explored_segments:
                # if more than 90% of segments have been explored, reset explored segments
                if len(LC_explored_segments) > 0.9* n_segments**2:
                    LC_explored_segments.clear()
                #print("LC segment already explored")
                continue

            #print("Exploring around cell", x, y)
            LC_explored_segments.append((x,y))
            self.target = (x, y)
            break

    # Robot actions
    def find_target(self):
        """
        Finds Debris within area and sets it as target.
        If no Debris found, continue.
        Return True if debris is found, else False
        """


        # Find Debris within area and sets it as target.
        debris = [a for a in self.model.schedule.agents if (isinstance(a,Debris) and a.state == UNDONE)]
        if debris == []:
            #print("No Target Found")
            #self.state = IDLE
            return False

        closest_debris = debris[0]
        for d in debris:
            if get_distance(self, d) < get_distance(self, closest_debris):
                closest_debris = d

        if get_distance(self, closest_debris) <= SCAN_RANGE:
            closest_debris.state = UNDERWAY
            self.target = (closest_debris.x, closest_debris.y, closest_debris.unique_id)
            self.state = PICKING
            return True
        else:
            return False


    def move_to_bin(self):
        """
        Set target to bin
        """
        self.state = EMPTYING
        bin = [a for a in self.model.schedule.agents if isinstance(a,WasteBin)]
        self.target = (bin[0].x, bin[0].y, bin[0].unique_id)


    def move(self):
        """
        Move robot to the next position.
        """
        self.model.grid.move_agent(self, (self.next_x, self.next_y))
        self.x = self.next_x
        self.y = self.next_y


    def wait(self):
        """
        Keep the same position as the current one.
        """
        self.next_x = self.x
        self.next_y = self.y


    def move_fw(self):
        """Move the robot towards the target"""
        x_dif = abs(self.x - self.target[0])
        y_dif = abs(self.y - self.target[1])

        if x_dif == 0 and y_dif == 0:
            self.state = IDLE

        if (x_dif > self.speed) and (self.target[0] > self.x):
            self.next_x = self.x + self.speed
        elif (x_dif > self.speed) and (self.target[0] < self.x):
            self.next_x = self.x - self.speed
        else:
            self.next_x = self.target[0]

        if (y_dif > self.speed) and (self.target[1] > self.y):
            self.next_y = self.y + self.speed
        elif (y_dif > self.speed) and (self.target[1] < self.y):
            self.next_y = self.y - self.speed
        else:
            self.next_y = self.target[1]

        # Obstacle avoidance using random movement
        if self.containsObstacle(self.next_x,self.next_y):
            print("next tile has an obstacle, changing next tile")
            
            while True:
                move = random.choice(["up","down","left","right"])
                if move == "up":
                    if self.containsObstacle(self.x,self.y+1) or self.y == NUMBER_OF_CELLS:
                        continue
                    self.next_y = self.y+1
                    break

                if move == "down":
                    if self.containsObstacle(self.x,self.y-1) or self.y == 0:
                        continue
                    self.next_y = self.y-1
                    break

                if move == "left":
                    if self.containsObstacle(self.x-1,self.y)or self.x == 0:
                        continue
                    self.next_x = self.x-1
                    break

                if move == "right":
                    if self.containsObstacle(self.x+1,self.y)or self.x == NUMBER_OF_CELLS:
                        continue
                    self.next_x = self.x+1
                    break

        self.move()

        
    def pick(self):
        """
        * change robot state to EMPTYING if overloaded
        * find out the id of the Debris next to the robot
        * Remove Debris from game
        * Add 1 to payload
        * If payload exceeds 50%, decrease speed
        * If returning to wastebin, set trail start
        """
        debris = [a for a in self.model.schedule.agents if isinstance(a,Debris) and a.unique_id==self.target[2]]
        self.payload += 1
        debris[0].state = DONE
        self.model.grid.remove_agent(debris[0])

        self.state = IDLE

        if self.payload >= 0.5*self.max_payload:
            self.speed = math.ceil(self.speed/2)

        # If maximum payload is exceeded set target to waste bin
        if self.payload >= self.max_payload:
            self.state = EMPTYING
            self.targetWasteBin()
            print("Heading towards waste bin at", self.target[0], self.target[1])
            self.trail_start = (self.x,self.y)
        else:
            self.target = None
            self.state = IDLE
    
    def drop_off(self):
        """
        * change state of the robot to IDLE
        * Set payload to 0
        * Remove target
        * Restore max speed
        """
        self.state = IDLE
               
        print("Emptying Cargo")
        self.payload = 0
        self.target = None
        self.speed = LC_SPEED
        self.last_placed = None
        self.move()
   
    def advance(self):
       """
       Advances position of the robot.
       """
       self.x = self.next_x
       self.y = self.next_y
    
    def containsObstacle(self, x,y):
        obstacles = [a for a in self.model.schedule.agents if isinstance(a,Obstacle) and a.x == x and a.y == y]
        if obstacles:
            return True
        else: 
            return False
        
    def create_job(self, ld):
        bd = [a for a in self.model.schedule.agents if isinstance(a,Bidder)][0]
        if ld not in bd.jobs:
            print("Creating job", ld)
            bd.jobs.append(ld)
    
    def place_pheromone(self):
        ph = Pheromone(id=self.model.n, pos=(self.x,self.y), model=self.model, next_ph=self.last_placed)

        self.last_placed = ph
        self.model.schedule.add(ph)
        try:
            self.model.grid.place_agent(ph,(self.x,self.y))
        except:
            self.model.grid.place_agent(ph,(abs(self.x-1),abs(self.y-1)))

        self.model.n += 1
        return

    def choose_trail(self):
        """
        * Chooses trail based on pheromones within scan range
        * Returns pheremone object
        """
        ph = [a for a in self.model.schedule.agents if isinstance(a,Pheromone) and get_distance(self, a) < SCAN_RANGE]
        print("Pheromones within range are:", ph)

        random_ph = random.choice(ph)
        return (random_ph)
        

class Bidder(mesa.Agent):
    """Agent that handles auctions"""
    def __init__(self, id, model, init_state=UNDONE):
        """
        Initialise
        """
        super().__init__(id, model)
        self.jobs = []               # List of Large Debris that has been discovered
        self.CT_list = []            # List of CTs available for bidding

    def update_jobs(self):
        """
        Removes UNDERWAY and DONE objects
        """
        for job in self.jobs:
            if job.state in (UNDERWAY, DONE):
                self.jobs.remove(job)
        #print("Jobs are now", self.jobs)


    def update_CT_info(self):
        """
        Updates CT information to current step
        """
        self.CT_list = [a for a in self.model.schedule.agents if (isinstance(a,CT_Robot) and (a.state == IDLE or a.state == EXPLORING) and a.reserve_target==None and len(a.payload) != 3)]
        #print("Bidding CTs are:", [x.unique_id for x in self.CT_list])

    def create_auction(self, job):
        """
        * Creates an auction for given job
        * Removes Job from list once assigned
        * If Job is not assigned remove it
        """

        # Assign job to winner using its unique_id
        def assign_winner(id):
            print("Assigning CT", id, "to job")
            winner_CT = [a for a in self.model.schedule.agents if (isinstance(a,CT_Robot) and a.unique_id==id)][0]
            winner_CT.target = (job.x, job.y, job.unique_id)
            job.state = UNDERWAY
            winner_CT.state = PICKING

        # Voting Methods  
        def plurality(CT_bid):
            """
            Assigns agent based on most votes.
            if multiple agents have the same votes the agent 2ith the lowest id will be assigned
            """
            for x in range(1, len(CT_bid.values())+1):
                # Get smallest value in column
                scores = ([i[x] for i in CT_bid.values()])
                smallest  = min(scores)
                highest_score = -1

                for (key, value) in CT_bid.items():
                    #print(key,value)
                    #print(CT_bid[key][x])

                    if value[0] > highest_score:
                        highest_score = value[0]
                        id = key

                    if CT_bid[key][x] == smallest:
                        new = list(value)
                        new[0] += 1
                        CT_bid[key] = tuple(new)

            return id
        
        def antiplurality(CT_bid):
            """
            Worst agent recieves votes and agent with the least votes gets assigned. 
            if multiple agents have the same votes the agent 2ith the lowest id will be assigned
            """
            for x in range(1, len(CT_bid.values())+1):
                # Get smallest value in column
                scores = ([i[x] for i in CT_bid.values()])
                largest  = max(scores)
                highest_score = 100000

                for (key, value) in CT_bid.items():
                    #print(key,value)
                    #print(CT_bid[key][x])

                    if value[0] < highest_score:
                        highest_score = value[0]
                        id = key

                    if CT_bid[key][x] == largest:
                        new = list(value)
                        new[0] += 1
                        CT_bid[key] = tuple(new)

            return id


        # If no CTs available remove job
        if not self.CT_list:
            print("No available agents for job")
            self.jobs.remove(job)
            return
        
        # If only 1 CT, assign it to job
        if len(self.CT_list) == 1:
            print("sole winner is:", self.CT_list[0])
            assign_winner(self.CT_list[0].unique_id)
            return
        
        CT_bid = {} # (Unique_id: Score, Distance to job, Charge Lost, Current Payload)
        for CT in self.CT_list:
            CT_bid[CT.unique_id] = (0, get_distance(job, CT), MAX_CHARGE - CT.charge, len(CT.payload))
        print("CT_bid is:", CT_bid)

        # Return id of winning CT
        match VOTING_TYPE:
            case "PLURALITY":
                winner = plurality(CT_bid)
            case "ANTIPLURALITY":
                winner = antiplurality(CT_bid)
            case _:
                winner = min(CT_bid, key=lambda t: t[1]) # Closest CT agent wins
        
        print("Winner is ", winner)
        assign_winner(winner)
        self.jobs.remove(job)
    
    def step(self):
        """
        * Checks if there are Jobs
        * Creates Auction for each Job based on CT Information
        """
        if self.model.EXTENDED:
            print("Bidder Step")
            if self.jobs:
                self.update_jobs()
                self.update_CT_info()

                while self.jobs:
                    print("Jobs are", self.jobs)
                    self.update_jobs()
                    self.update_CT_info()
                    if self.jobs:
                        self.create_auction(self.jobs[0])



class LargeDebris(mesa.Agent):
    """Represents a large piece of debris on the beach."""
    def __init__(self, id, pos, model, init_state=UNDONE):
        """
        Intialise state and position of the Debris
        """
        super().__init__(id, model)
        self.state = UNDONE
        self.x, self.y = pos

class Debris(mesa.Agent):
    """Represents patch of sand containing small debris on the beach."""
    def __init__(self, id, pos, model, init_state=UNDONE):
        """
        Intialise state and position of the Debris
        """
        super().__init__(id, model)
        self.state = UNDONE
        self.x, self.y = pos

class WasteBin(mesa.Agent):
    """Represents a Waste Bin where robots deposit waste."""
    def __init__(self, id, pos, model):
        """
        Intialise position of the Waste Bin
        """
        super().__init__(id, model)
        self.x, self.y = pos

class ChargingPoint(mesa.Agent):
    """Represents a Charging Point where CT robots recharge."""
    def __init__(self, id, pos, model):
        """
        Intialise position of the Charging Station
        """
        super().__init__(id, model)
        self.x, self.y = pos

class Obstacle(mesa.Agent):
    """Represents an Obstacle where robots cannot move to."""
    def __init__(self, id, pos, model):
        """
        Intialise position of the Obstacle
        """
        super().__init__(id, model)
        self.x, self.y = pos

class Pheromone(mesa.Agent):
    """ A Pheremone generated by an LC agent while returning to the wastebin"""
    def __init__(self, id, pos, model, next_ph):
        """
        Initialise position of the Pheromone
        """
        super().__init__(id, model)
        self.x, self.y = pos
        self.next_ph = next_ph        # Previous pheromone in trail
        self.strength = pheromone_strength    # Represents how recent the pheromone was placed, decreases overtime to 0 then pheromone is removed
        if self.next_ph:
            print("placing pheromone, next in trail is", self.next_ph.x, self.next_ph.y)

    def step(self):
        #print("Pheromone", self.unique_id, "strength is:", self.strength, "position is:", self.x, self.y, "target is:", self.target)
        self.strength -= 1

        if self.strength <= 0:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)


# Global Functions
def get_distance(obj1, obj2):
    """
    Uses the manhattan distance for simplification.
    """
    return abs(obj1.x - obj2.x) + abs(obj1.y - obj2.y)
