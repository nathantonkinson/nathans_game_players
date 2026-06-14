#pip install pysr
# import pysr
from pysr import PySRRegressor
import numpy as np

x = 2*np.random.randn(100,5)
y = 2.5382 * np.cos(x[:, 3]) + x[:, 0] ** 2 - 0.5

# model = PySRRegressor(
#     maxsize=20,
#     niterations=40,  # < Increase me for better results
#     binary_operators=["+", "*"],
#     unary_operators=[
#         "cos",
#         "exp",
#         "sin",
#         "inv(x) = 1/x",
#         # ^ Custom operator (julia syntax)
#     ],
#     extra_sympy_mappings={"inv": lambda x: 1 / x},
#     # ^ Define operator for SymPy as well
#     elementwise_loss="loss(prediction, target) = (prediction - target)^2",
#     # ^ Custom loss function (julia syntax)
# )
