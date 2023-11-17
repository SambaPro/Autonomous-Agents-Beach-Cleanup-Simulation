# Make a world that is 50x50, on a 250x250 display.
import mesa
from beach.model import Beach
from .portrayal import beach_portrayal
from .agents import NUMBER_OF_CELLS

SIZE_OF_CANVAS_IN_PIXELS_X = 400
SIZE_OF_CANVAS_IN_PIXELS_Y = 400

LC_NUM = 2
CT_NUM = 2
NUMBER_OF_LARGE_DEBRIS = 8
NUMBER_OF_DEBRIS = 500
NUMBER_OF_OBSTACLES = 20

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
    "n_Ldebris":mesa.visualization.Slider(
        'number_of_large_debris',
        NUMBER_OF_LARGE_DEBRIS, #default
        1, #min
        20, #max
        1, #step
        description="choose how many Large Debris to include in the simulation",
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
        50, #min
        1000, #max
        10, #step
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
grid = mesa.visualization.CanvasGrid(beach_portrayal, NUMBER_OF_CELLS, NUMBER_OF_CELLS, SIZE_OF_CANVAS_IN_PIXELS_X, SIZE_OF_CANVAS_IN_PIXELS_Y)


server = mesa.visualization.ModularServer(
    Beach, [grid], "Beach", simulation_params
)