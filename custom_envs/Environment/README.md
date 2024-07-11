using Pkg
Pkg.rm("KiteModels")

Pkg.add(url="https://github.com/yourusername/KiteModels.jl")

usage in code:
using KiteModels

Pkg.update("KiteModels") to update commits done to KiteModels


command to run training:
python train.py --algo ars --env KiteEnv-v3 --eval-episodes 10 --eval-freq 200000 -n 200000000 -tb tb-log


hyperparam tuning:
python train.py --algo ars --env KiteEnv-v3 -optimize --study-name kite_env-v3-2 --storage sqlite:///kite_env-v3.db --n-trials 1000 --n-jobs 1 -n 50000 --eval-episodes 1 --n-evaluations 10 --verbose 2

hyperparam viewing:
 python scripts/parse_study.py --study-name kite_env-v3-2 --print-n-best-trials 10 --storage sqlite:///kite_env-v3.db


ConnectionResetError