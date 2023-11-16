# Make a world that is 50x50, on a 250x250 display.
import mesa
from warehouse.model import Warehouse
from .portrayal import warehouse_portrayal
from .agents import NUMBER_OF_CELLS

SIZE_OF_CANVAS_IN_PIXELS_X = 300
SIZE_OF_CANVAS_IN_PIXELS_Y = 300

LC_NUM = 2
CT_NUM = 2
NUMBER_OF_BOXES = 8
NUMBER_OF_DEBRIS = 10
NUMBER_OF_OBSTACLES = 20

# TODO Add a parameter named "n_boxes" for the number of boxes to include in the model.
simulation_params = {
    "height": NUMBER_OF_CELLS, 
    "width": NUMBER_OF_CELLS,
    "n_CT_robots": mesa.visualization.Slider(
        'number of CTs',
        CT_NUM, #default
        0, #min
        3, #max
        1, #step
        "choose how many CT robots to include in the simulation"
    ),
    "n_boxes":mesa.visualization.Slider(
        'number_of_boxes',
        NUMBER_OF_BOXES, #default
        1, #min
        20, #max
        1, #step
        description="choose how many boxes to include in the simulation",
    ),
    "n_obstacles":mesa.visualization.Slider(
        'number_of_obstacles',
        NUMBER_OF_OBSTACLES, #default
        0, #min
        50, #max
        1, #step
        description="choose how many obstacles to include in the simulation",
    ),
    "n_debris":mesa.visualization.Slider(
        'number_of_debris',
        NUMBER_OF_DEBRIS, #default
        10, #min
        100, #max
        1, #step
        description="choose how many piles of debris to include in the simulation",
    ),
    "n_LC_robots":mesa.visualization.Slider(
        'number_of_LCs',
        LC_NUM, #default
        0, #min
        10, #max
        1, #step
        description="choose how many LC robots to include in the simulation",
    )
}
grid = mesa.visualization.CanvasGrid(warehouse_portrayal, NUMBER_OF_CELLS, NUMBER_OF_CELLS, SIZE_OF_CANVAS_IN_PIXELS_X, SIZE_OF_CANVAS_IN_PIXELS_Y)


server = mesa.visualization.ModularServer(
    Warehouse, [grid], "Modern Warehouse", simulation_params
)