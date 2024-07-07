using Pkg
Pkg.rm("KiteModels")

Pkg.add(url="https://github.com/yourusername/KiteModels.jl")

usage in code:
using KiteModels

Pkg.update("KiteModels") to update commits done to KiteModels


command to run training:
python train.py --algo ars --env KiteEnv-v3 --eval-episodes 10 --eval-freq 200000 -n 200000000 -tb tb-log
