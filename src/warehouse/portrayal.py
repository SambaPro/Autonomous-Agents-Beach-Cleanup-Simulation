from warehouse.agents import PickerRobot
from warehouse.agents import Box


def warehouse_portrayal(agent):
   """
   Determine which portrayal to use according to the type of agent.
   """
   if isinstance(agent,PickerRobot):
        return robot_portrayal(agent)
   else:
        return box_portrayal(agent)

def robot_portrayal(robot):

    if robot is None:
        raise AssertionError
    return {
        "Shape": "arrowHead",
        "w": 1,
        "h": 1,
        "Filled": "true",
        "Layer": 0,
        "x": robot.x,
        "y": robot.y,
        "scale": 2,
        "heading_x": -1 if robot.isBusy else 1,
        "heading_y":0,
        # "r":4,
        "Color": "red" if robot.isBusy else "green",
    }

def box_portrayal(box):

    if box is None:
        raise AssertionError
    return {
        "Shape": "rect",
        "w": 1,
        "h": 1,
        "Filled": "true",
        "Layer": 0,
        "x": box.x,
        "y": box.y,
        "Color": "blue",
    }