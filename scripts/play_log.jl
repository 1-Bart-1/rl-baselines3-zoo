using KiteModels, Serialization, ControlPlots

if ! @isdefined kcu;  const kcu = KCU(se());   end
if ! @isdefined s; const s = KPS4_3L(kcu); end

set_data_path(joinpath(dirname(@__FILE__), "../logs/ars/KiteEnv-v1_25"))
# set_data_path(joinpath(dirname(@__FILE__), "../custom_envs/Environment/data"))
name = "sim_log"
path = joinpath(get_data_path(), name) * ".bin"
logger = deserialize(path)

for i in eachindex(logger)
    plot2d(logger[i], i*0.05 ; zoom=false, front=false)
end
# # the following values can be changed to match your interest
# dt = 0.05
# TIME_LAPSE_RATIO = 1      # 1 = realtime, 2..8 faster
# set_data_path(joinpath(dirname(@__FILE__), "../logs/ars/KiteEnv-v1_25"))
# LOG_FILE_NAME = "12-06-24" # without extension!
# PARTICLES = 6 + 5         # 7 for tether and KCU, 4 for the kite
# # end of user parameter section #

# log=load_log(PARTICLES, LOG_FILE_NAME)
# print(log.syslog)

# if ! @isdefined viewer; const viewer = Viewer3D(true); end

# function play(syslog)
#     steps = length(syslog.time)
#     start_time_ns = time_ns()
#     KiteViewers.clear_viewer(viewer)
#     for i in 1:steps
#         if mod(i, TIME_LAPSE_RATIO) == 0 || i == steps
#             update_system(viewer, syslog[i]; scale = 0.08, kite_scale=3.0)
#             # save_png(viewer, index=div(i, TIME_LAPSE_RATIO))
#             wait_until(start_time_ns + dt*1e9, always_sleep=true)
#             start_time_ns = time_ns()
#         end
#     end
# end


# play(log.syslog)
# stop(viewer)
