using Pkg
Pkg.rm("KiteModels")

Pkg.add(url="https://github.com/yourusername/KiteModels.jl")

usage in code:
using KiteModels

Pkg.update("KiteModels") to update commits done to KiteModels