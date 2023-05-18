import os, sys
sys.path.append(str(os.path.dirname(__file__)))
from shape_pretraining import ShapePretrainingTaskNoRegressionPocket
from mol_gen.benchmark import LIB_PATH

config = LIB_PATH + "/configs/desert/sample.yml"


# ShapePretrainingTaskNoRegressionPocket()