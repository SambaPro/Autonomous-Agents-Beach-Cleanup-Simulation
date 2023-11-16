from optparse import check_builtin
import mesa
import random
import math

""" Beach Parameters"""
NUMBER_OF_CELLS = 50
n = 0
n_segments = 10           # Must be large otherwise agents may miss areas/debris
explored_segments = []    # Makes it more likely that unexplored segments will be targeted

""" Agent States """
FREE = 0              # Idle (Default State)
EXPLORING = 1         # Exploring in random direction and magnitude
EMPTYING = 2          # Moving towards wastebin / Emptying cargo
CHARGING = 3          # Moving towards charging point/ Waiting to be fully charged
PICKING = 4           # Moving to target

""" Box States """
UNDONE = 0
UNDERWAY = 2
DONE = 1

""" Agent Parameters """
# General Parameters
SCAN_RANGE = 5

# CR Parameters
CR_MAX_PAYLOAD = 3
CR_SPEED = 1
NEEDS_CHARGE = True
MAX_CHARGE = 300     # Maximum and starting charge, will decrease by 1 for each tile traversed
MIN_CHARGE = 100     # When agent reaches this charge level, they will return to charging station
CHARGING_SPEED = 50  # Charge restored each step once at charging station

# LC Parameters
LC_MAX_PAYLOAD = 5
LC_SPEED = 3


class CT_Robot(mesa.Agent):
    """Represents a Robot of the warehouse."""
    def __init__(self, id, pos, model, max_payload=CR_MAX_PAYLOAD, speed=CR_SPEED, init_state=FREE):
        """
        Initialise state attributes, including:
          * current and next position of the robot
          * state (FREE/BUSY)
          * payload (id of any box the robot is carrying)
        """
        super().__init__(id, model)
        self.x, self.y = pos
        self.next_x, self.next_y = None, None
        self.state = init_state
        self.payload = []
        self.max_payload = max_payload
        self.speed = speed
        self.target = None # (x,y,unique_id)
        self.charge = MAX_CHARGE

    @property
    def isBusy(self):
        return (self.state==EXPLORING or self.state == PICKING)
  
    @property
    def atChargingPoint(self):
        chp = [a for a in self.model.schedule.agents if isinstance(a,ChargingPoint)]
        #print("Charging point is at", chp[0].x, chp[0].y, "Robot is at", self.x, self.y)
        return (self.x == chp[0].x and self.y == chp[0].y)
    
    @property
    def atWasteBin(self):
        wb = [a for a in self.model.schedule.agents if isinstance(a,WasteBin)]
        return self.x == wb[0].x and self.y == wb[0]
    
    def targetChargingPoint(self):
        chp = [a for a in self.model.schedule.agents if isinstance(a,ChargingPoint)]
        self.target = (chp[0].x, chp[0].y, chp[0].unique_id)

    def targetWasteBin(self):
        wb = [a for a in self.model.schedule.agents if isinstance(a,WasteBin)]
        self.target = (wb[0].x, wb[0].y, wb[0].unique_id)

    def BoxesLeft(self):
        boxes = [a for a in self.model.schedule.agents if (isinstance(a,Box) and (a.state == UNDONE or self.state == UNDERWAY))]
        return len(boxes) != 0


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
        print("CT", self.unique_id, "state is:", self.state)
        print("CT", self.unique_id, "position is: ", self.x, ",", self.y)
        if self.target:
            print("CT", self.unique_id, "target is at:", self.target[0], self.target[1])
        print("CT", self.unique_id, "payload is:", len(self.payload))
        print("Payload contains", self.payload)

        # When all boxes are busy
        action = "wait"
        if not self.BoxesLeft() and self.payload and self.state == FREE:
            print("there are no boxes left to do")
            print("Moving Payload to waste bin")
            action = "move_to_bin"
            self.state = EMPTYING
            return action
        
        elif not self.BoxesLeft() and self.state == FREE:
            print("there are no boxes left to do")
            self.state = CHARGING
            action = "goto_charging_station"
            return action

        elif self.state == EXPLORING:
            if not self.target:
                self.set_explore_target()
            elif self.x == self.target[0] and self.y == self.target[1]:
                if self.charge < MIN_CHARGE:
                    self.state = CHARGING
                else:
                    self.set_explore_target()

            if self.find_target(): # Target within range
                self.state = PICKING
            else:
                action = "move_fw"

        elif self.state == CHARGING:
            if self.charge >= MAX_CHARGE:
                self.state = FREE
                self.charge = MAX_CHARGE

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

        elif self.state == FREE:
            if self.charge < 100:
                print("moving to charging point")
                action = "goto_charging_station"
            elif len(self.payload) > self.max_payload:
                print("moving to bin")
                action = "move_to_bin"
            elif self.BoxesLeft():
                print("Robot is now exploring")
                self.state = EXPLORING
            else:
                self.state = CHARGING

        elif self.state == PICKING:
            if (self.x == self.target[0]) and (self.y == self.target[1]):
                print("Robot is now picking")
                action = "pick"
            else:
                print("Robot is now moving forwards")
                action = "move_fw"
        else:
            print("Robot is now returning to charging station")
            action = "goto_charging_station" # Return to base
        return action

    def set_explore_target(self):
        """
        Splits map into segments and sets the target to segment centre
        """
        while True:
            x_segment = random.randint(1, n_segments)
            y_segment = random.randint(1, n_segments)

            x = math.floor(x_segment*NUMBER_OF_CELLS/(n_segments))-1
            y = math.floor(y_segment*NUMBER_OF_CELLS/(n_segments))-1

            if self.containsObstacle(x,y):
                print("cell contains obstacle, finding new one")
                continue
            if (x,y) in explored_segments:
                if len(explored_segments) > 0.75* n_segments**2:
                    explored_segments.clear()
                print("CT segment already explored")
                continue
            print("Exploring around cell", x, y)
            explored_segments.append((x,y))
            self.target = (x, y)
            break

    # Robot actions
    def find_target(self):
        """
        Finds box within area and sets it as target.
        If no box found, continue exploring.
        """
        boxes = [a for a in self.model.schedule.agents if (isinstance(a,Box) and (a.unique_id not in self.payload) and a.state == UNDONE)]

        if boxes == []:
            print("No Target Found")
            self.state = FREE
            return False

        # Get closes box
        closest_box = boxes[0]
        for box in boxes:
            if self.get_distance(box) < self.get_distance(closest_box):
                closest_box = box
                #print("closest box is at", closest_box.x, closest_box.y) 

        if self.get_distance(closest_box) <= SCAN_RANGE:
            closest_box.state = UNDERWAY
            self.target = (closest_box.x, closest_box.y, closest_box.unique_id)
            self.state = PICKING
            return True
        else:
            return False


    def move_to_bin(self):
        self.state = EMPTYING
        bin = [a for a in self.model.schedule.agents if isinstance(a,WasteBin)]
        self.target = (bin[0].x, bin[0].y, bin[0].unique_id)

    def goto_charging_station(self):
        self.state = CHARGING
        chp = [a for a in self.model.schedule.agents if isinstance(a,ChargingPoint)]
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
        print("CT",self.unique_id, "charge is now",self.charge)

        if self.charge < MIN_CHARGE and not self.target:
            self.state = CHARGING


    def move_payload(self):
        """
        * Obtains the box whose id is in the payload (Hint: you can use the method: self.model.schedule.agents to iterate over existing agents.)
        * move the payload together with the robot
        """
        boxes = [a for a in self.model.schedule.agents if isinstance(a,Box) and a.unique_id in self.payload]
        for box in boxes:
            self.model.grid.move_agent(box,(self.x,self.y))


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
            self.state = FREE

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
        * change robot state to Busy if overloaded
        * find out the id of the box next to the robot
        * store the box id in the payload of the robot
        """
        box = [a for a in self.model.schedule.agents if isinstance(a,Box) and a.unique_id==self.target[2]]
        box[0].state = UNDERWAY
        self.payload.append(self.target[2])

        # If maximum payload is exceeded set target to waste bin
        if len(self.payload) >= self.max_payload:
            self.state = EMPTYING
            wb = [a for a in self.model.schedule.agents if isinstance(a,WasteBin)]
            self.target = (wb[0].x, wb[0].y, wb[0].unique_id)
            print("Heading towards waste bin at", self.target[0], self.target[1])
        else:
            self.target = None
            self.state = FREE
    
    def drop_off(self):
        """
        * change state of the robot to Free
        * Get the Box whose id is in the payload and remove it from the grid and change its state to Done.
        * Remove payload from robot
        """
        self.state = FREE
        boxes = [a for a in self.model.schedule.agents if isinstance(a,Box) and a.unique_id in self.payload]
        
        print("Removing Box/s from game")
        for box in boxes:
            box.state = DONE
            self.model.grid.remove_agent(box)
        
        self.payload = []
        self.target = None
        self.move()
   
    def advance(self):
       """
       Advances position of the robot.
       """
       self.x = self.next_x
       self.y = self.next_y

    def get_distance(self, box):
        """
        Uses the manhattan distance for simplification.
        """
        return abs(self.x - box.x) + abs(self.y - box.y)
    
    def containsObstacle(self, x,y):
        obstacles = [a for a in self.model.schedule.agents if isinstance(a,Obstacle) and a.x == x and a.y == y]
        if obstacles:
            return True
        else: 
            return False
    
class LC_Robot(mesa.Agent):
    """Represents a Robot of the warehouse."""
    def __init__(self, id, pos, model, max_payload=LC_MAX_PAYLOAD, speed=LC_SPEED, init_state=FREE):
        """
        Initialise state attributes, including:
          * current and next position of the robot
          * state (FREE/BUSY)
          * payload (id of any box the robot is carrying)
        """
        super().__init__(id, model)
        self.x, self.y = pos
        self.next_x, self.next_y = None, None
        self.state = init_state
        self.payload = 0
        self.max_payload = max_payload
        self.speed = speed
        self.target = None # (x,y,unique_id)


    @property
    def isBusy(self):
        return (self.state==EXPLORING or self.state == PICKING)
  
    @property
    def atChargingPoint(self):
        chp = [a for a in self.model.schedule.agents if isinstance(a,ChargingPoint)]
        #print("Charging point is at", chp[0].x, chp[0].y, "Robot is at", self.x, self.y)
        return (self.x == chp[0].x and self.y == chp[0].y)
    
    @property
    def atWasteBin(self):
        wb = [a for a in self.model.schedule.agents if isinstance(a,WasteBin)]
        return self.x == wb[0].x and self.y == wb[0]
    
    def targetChargingPoint(self):
        chp = [a for a in self.model.schedule.agents if isinstance(a,ChargingPoint)]
        self.target = (chp[0].x, chp[0].y, chp[0].unique_id)

    def targetWasteBin(self):
        wb = [a for a in self.model.schedule.agents if isinstance(a,WasteBin)]
        self.target = (wb[0].x, wb[0].y, wb[0].unique_id)

    def DebrisLeft(self):
        debris = [a for a in self.model.schedule.agents if (isinstance(a,Debris) and (a.state == UNDONE))]
        return len(debris) != 0

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
        print("LC", self.unique_id, "state is:", self.state)
        print("LC", self.unique_id, "position is: ", self.x, ",", self.y)
        if self.target:
            print("LC", self.unique_id, "target is at:", self.target[0], self.target[1])
        print("Payload is", self.payload)

        # When all boxes are busy
        action = "wait"
        if not self.DebrisLeft() and self.state == FREE:
            print("there are no boxes left to do")
            return action
        elif not self.DebrisLeft() and self.payload and self.state == FREE:
            print("there are no boxes left to do")
            print("Moving Payload to waste bin")
            action = "move_to_bin"
            return action

        elif self.state == EXPLORING:
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
                print("moving towards waste bin")
                action = "move_fw"

        elif self.state == FREE:
            if self.payload >= self.max_payload:
                print("moving to bin")
                action = "move_to_bin"
            elif self.DebrisLeft():
                print("Robot is now exploring")
                self.state = EXPLORING
            else:
                self.state = FREE

        elif self.state == PICKING:
            if (self.x == self.target[0]) and (self.y == self.target[1]):
                print("Robot is now picking")
                action = "pick"
            else:
                print("Robot is now moving forwards")
                action = "move_fw"
        else:
            print("Robot is now returning to charging station")
            action = "goto_charging_station" # Return to base
        return action


    # Robot actions
    def set_explore_target(self):
        """
        Splits map into segments and sets the target to segment centre
        """
        while True:
            x_segment = random.randint(1, n_segments)
            y_segment = random.randint(1, n_segments)

            x = math.floor(x_segment*NUMBER_OF_CELLS/(n_segments))-1
            y = math.floor(y_segment*NUMBER_OF_CELLS/(n_segments))-1

            if self.containsObstacle(x,y):
                print("cell contains obstacle, finding new one")
                continue
            #if (x,y) in explored_segments:
            #    print("LC segment already explored")
            #    continue
            print("Exploring around cell", x, y)
            explored_segments.append((x,y))
            self.target = (x, y)
            break

    # Robot actions
    def find_target(self):
        """
        Finds box within area and sets it as target.
        If no box found, continue exploring.
        """
        debris = [a for a in self.model.schedule.agents if (isinstance(a,Debris) and a.state == UNDONE)]

        if debris == []:
            print("No Target Found")
            self.state = FREE
            return False

        # Get closes debris
        closest_debris = debris[0]
        for d in debris:
            if self.get_distance(d) < self.get_distance(closest_debris):
                closest_debris = d
                #print("closest box is at", closest_box.x, closest_box.y) 

        if self.get_distance(closest_debris) <= SCAN_RANGE:
            closest_debris.state = UNDERWAY
            self.target = (closest_debris.x, closest_debris.y, closest_debris.unique_id)
            self.state = PICKING
            return True
        else:
            return False


    def move_to_bin(self):
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
            self.state = FREE

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
        * change robot state to Busy if overloaded
        * find out the id of the box next to the robot
        * store the box id in the payload of the robot
        """
        debris = [a for a in self.model.schedule.agents if isinstance(a,Debris) and a.unique_id==self.target[2]]
        self.payload += 1
        self.model.grid.remove_agent(debris[0])

        self.state = FREE

        # If maximum payload is exceeded set target to waste bin
        if self.payload >= self.max_payload:
            self.state = EMPTYING
            wb = [a for a in self.model.schedule.agents if isinstance(a,WasteBin)]
            self.target = (wb[0].x,wb[0].y, wb[0].unique_id)
            print("Heading towards waste bin at", self.target[0], self.target[1])
        else:
            self.target = None
            self.state = FREE
    
    def drop_off(self):
        """
        * change state of the robot to Free
        * Get the Box whose id is in the payload and remove it from the grid and change its state to Done.
        * Remove payload from robot
        """
        self.state = FREE
               
        print("Emptying Cargo")
        self.payload = 0
        self.target = None
        self.move()
   
    def advance(self):
       """
       Advances position of the robot.
       """
       self.x = self.next_x
       self.y = self.next_y

    def get_distance(self, box):
        """
        Uses the manhattan distance for simplification.
        """
        return abs(self.x - box.x) + abs(self.y - box.y)
    
    def containsObstacle(self, x,y):
        obstacles = [a for a in self.model.schedule.agents if isinstance(a,Obstacle) and a.x == x and a.y == y]
        if obstacles:
            return True
        else: 
            return False

class Box(mesa.Agent):
    """Represents a Box in the warehouse."""
    def __init__(self, id, pos, model, init_state=UNDONE):
        """
        Intialise state and position of the box
        """
        super().__init__(id, model)
        self.state = UNDONE
        self.x, self.y = pos

class Debris(mesa.Agent):
    """Represents patch of sand containing debris in the warehouse."""
    def __init__(self, id, pos, model, init_state=UNDONE):
        """
        Intialise state and position of the box
        """
        super().__init__(id, model)
        self.state = UNDONE
        self.x, self.y = pos

class WasteBin(mesa.Agent):
    """Represents a Waste Bin where robots deposit waste."""
    def __init__(self, id, pos, model, init_state=UNDONE):
        """
        Intialise state and position of the box
        """
        super().__init__(id, model)
        self.x, self.y = pos

class ChargingPoint(mesa.Agent):
    """Represents a Waste Bin where robots deposit waste."""
    def __init__(self, id, pos, model, init_state=UNDONE):
        """
        Intialise state and position of the box
        """
        super().__init__(id, model)
        self.x, self.y = pos

class Obstacle(mesa.Agent):
    """Represents a Waste Bin where robots deposit waste."""
    def __init__(self, id, pos, model, init_state=UNDONE):
        """
        Intialise state and position of the box
        """
        super().__init__(id, model)
        self.x, self.y = pos