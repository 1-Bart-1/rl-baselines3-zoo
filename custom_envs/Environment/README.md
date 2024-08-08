using Pkg
Pkg.rm("KiteModels")

Pkg.add(url="https://github.com/yourusername/KiteModels.jl")

usage in code:
using KiteModels

Pkg.update("KiteModels") to update commits done to KiteModels


command to run training:
python train.py --algo ars --env KiteEnv-v3 --eval-episodes 20 --eval-freq 500000 -n 200000000 -tb tb-log


hyperparam tuning:
python train.py --algo ars --env KiteEnv-v3 -optimize --study-name kite_env-v3-3 --storage sqlite:///kite_env-v3.db --n-trials 1000 --n-jobs 1 -n 500000 --eval-episodes 1 --n-evaluations 20 --verbose 2

hyperparam viewing:
python scripts/parse_study.py --study-name kite_env-v3-3 --print-n-best-trials 10 --storage sqlite:///kite_env-v3.db


ConnectionResetError


ars_23 / v3_55 WORKS with 3Hz sampling
v3_59 WORKS with 3Hz sampling

logs/ars/KiteEnv-v3_66 && tb-log/KiteEnv-v3/ARS_31: probably was 20Hz...
logs/ars/KiteEnv-v3_67 && tb-log/KiteEnv-v3/ARS_32: actually 3Hz. Should be almost twice as fast relatively.
logs/ars/KiteEnv-v3_69 && tb-log/KiteEnv-v3/ARS_33: actually 3Hz. Same rewards as 20Hz.
logs/ars/KiteEnv-v3_74 && tb-log/KiteEnv-v3/ARS_36: seed all envs the same for each episode. works really well
tb-log/KiteEnv-v3/ARS_39 && logs/ars/KiteEnv-v3_77: new tether model. using torque * 100, 3hz, no reward
tb-log/KiteEnv-v3/ARS_43 && logs/ars/KiteEnv-v3_82: using torque * 10, 20hz, 
tb-log/KiteEnv-v3/ARS_44 && logs/ars/KiteEnv-v3_83: using torque * 10, 20hz, stable tether length, sample freq defined wrong in kite env (3hz). almost 1000fps. short episodes because of wrong sample freq.
tb-log/KiteEnv-v3/ARS_45 && logs/ars/KiteEnv-v3_84: sample freq corrected, torque*10 and assert steering pos is correct.