using Pkg
Pkg.rm("KiteModels")

Pkg.add(url="https://github.com/yourusername/KiteModels.jl")

usage in code:
using KiteModels

Pkg.update("KiteModels") to update commits done to KiteModels


command to run training:
python train.py --algo ars --env KiteEnv-v3 --eval-episodes 20 --eval-freq 100000 -n 200000000 -tb tb-log


hyperparam tuning:
python train.py --algo ars --env KiteEnv-v3 -optimize --study-name kite_env-v3-4 --storage sqlite:///kite_env-v3.db --n-trials 1000 --n-jobs 1 -n 500000 --eval-episodes 1 --n-evaluations 20 --verbose 2

hyperparam viewing:
python scripts/parse_study.py --study-name kite_env-v3-4 --print-n-best-trials 10 --storage sqlite:///kite_env-v3.db


optimize path and optimize heading following seperately


ars_23 / v3_55 WORKS with 3Hz sampling
v3_59 WORKS with 3Hz sampling

logs/ars/KiteEnv-v3_66 && tb-log/KiteEnv-v3/ARS_31: probably was 20Hz...
logs/ars/KiteEnv-v3_67 && tb-log/KiteEnv-v3/ARS_32: actually 3Hz. Should be almost twice as fast relatively.
logs/ars/KiteEnv-v3_69 && tb-log/KiteEnv-v3/ARS_33: actually 3Hz. Same rewards as 20Hz.
logs/ars/KiteEnv-v3_74 && tb-log/KiteEnv-v3/ARS_36: seed all envs the same for each episode. works really well
tb-log/KiteEnv-v3/ARS_39 && logs/ars/KiteEnv-v3_77: new tether model. using torque * 100, 3hz, no reward
tb-log/KiteEnv-v3/ARS_43 && logs/ars/KiteEnv-v3_82: using torque * 10, 20hz, 
tb-log/KiteEnv-v3/ARS_44 && logs/ars/KiteEnv-v3_83: using torque * 10, 20hz, stable tether length, sample freq defined wrong in kite env (3hz). almost 1000fps. short episodes because of wrong sample freq.
tb-log/KiteEnv-v3/ARS_45 && logs/ars/KiteEnv-v3_84: sample freq corrected, torque*10 and assert steering pos is correct. gets stuck at 70 frames. Torque * 10 is too low. It gets stuck at max torque.
tb-log/KiteEnv-v3/ARS_48 && logs/ars/KiteEnv-v3_87: Increase torque to 100. Reward=0 if kite goes backwards. Works really well. 3000fps. 1201 steps. Tethers get really loose, steering_force was 0.1.
tb-log/KiteEnv-v3/ARS_49 && logs/ars/KiteEnv-v3_88: Increase tether force to 0.2. Decrease tether diameter to 0.7mm. Used wrong settings maybe.
tb-log/KiteEnv-v3/ARS_50 && logs/ars/KiteEnv-v3_89: Change settings name to settings.yaml and add simlink to settings.yaml. Still max action after training for a while.
tb-log/KiteEnv-v3/ARS_51 && logs/ars/KiteEnv-v3_90: Increase torque multiplier to 1000. Boring kite.
tb-log/KiteEnv-v3/ARS_52 && logs/ars/KiteEnv-v3_91: Give reward to make kite turn. Didnt work so well.
tb-log/KiteEnv-v3/ARS_55 && logs/ars/KiteEnv-v3_95: Only reward if higher than max. Has to improve. 
tb-log/KiteEnv-v3/ARS_56 && logs/ars/KiteEnv-v3_96: Only reward if higher than 0.9 max
tb-log/KiteEnv-v3/ARS_57 && logs/ars/KiteEnv-v3_97: Reward with speed.
tb-log/KiteEnv-v3/ARS_59 && logs/ars/KiteEnv-v3_99: Reward with speed. No prints.
30 seconds and 10000 multiplier.
tb-log/KiteEnv-v3/ARS_64 && logs/ars/KiteEnv-v3_105: 10 seconds and 1000 multiplier.
108: it works! use speed for reward and use reward = min(reward, 1.0)
109: increase max reward slightly when truncated. still using speed for reward. works at 4.5 million steps. should reduce the reward increase a bit.
110: negative reward for flying backwards. bit chaotic flying, not finishing episode.
111: reduce reward increase a bit, increase negative crash reward
112: decrease multiplier to 300. decrease damping for steering lines. remove reward multiplier which makes crashing more expensive
113: lower start reward.
115: reward direction. doesnt work: shorter episode is bigger reward. cannot give negative rewards before end of episode. could use:     
    reward = normalize(s.pos[s.num_A]) ⋅ wanted_direction + 1.0
116: faster solver, little reward for doing wrong things as well, using formula above, checked and speed can be positive from the start, stiffness=1 from start.
117: move wanted azimuth a bit
120: lot more std dev, 60 delta

tb-log/KiteEnv-v3/ARS_80, logs/ars/KiteEnv-v3_129: new model
logs/ars/KiteEnv-v3_131, tb-log/KiteEnv-v3/ARS_82: fixed ram pressure
136: works really well, but spinning like crazy
140: works
147: not so good
148: 
150: works, slower than with normalized
155: local maximum
156: bigger reward range