from warehouse.agents import CT_Robot
from warehouse.agents import Box
from warehouse.agents import WasteBin
from warehouse.agents import ChargingPoint
from warehouse.agents import Obstacle


def warehouse_portrayal(agent):
   """
   Determine which portrayal to use according to the type of agent.
   """
   if isinstance(agent,CT_Robot):
        return CT_portrayal(agent)
   elif isinstance(agent, WasteBin):
       return wastebin_portrayal(agent)
   elif isinstance(agent, ChargingPoint):
       return chargingpoint_portrayal(agent)
   elif isinstance(agent, Obstacle):
       return obstacle_portrayal(agent)
       
   else:
        return box_portrayal(agent)

def CT_portrayal(CT):
    if CT is None:
        raise AssertionError
    return {
        "Shape": "arrowHead",
        "w": 1,
        "h": 1,
        "Filled": "true",
        "Layer": 0,
        "x": CT.x,
        "y": CT.y,
        "scale": 2,
        "heading_x": -1 if CT.isBusy else 1,
        "heading_y":0,
        # "r":4,
        "Color": "red" if CT.isBusy else "green",
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

def wastebin_portrayal(wb):
    if wb is None:
        raise AssertionError
    return {
        "Shape": "rect",
        "w": 1,
        "h": 1,
        "Filled": "true",
        "Layer": 0,
        "x": wb.x,
        "y": wb.y,
        "Color": "blue",
    }

def chargingpoint_portrayal(chp):
    if chp is None:
        raise AssertionError
    return {
        "Shape": "rect",
        "w": 1,
        "h": 1,
        "Filled": "true",
        "Layer": 0,
        "x": chp.x,
        "y": chp.y,
        "Color": "blue",
    }

def obstacle_portrayal(obst):
    if obst is None:
        raise AssertionError
    return {
        "Shape": "rect",
        "w": 1,
        "h": 1,
        "Filled": "true",
        "Layer": 0,
        "x": obst.x,
        "y": obst.y,
        "Color": "black",
    }