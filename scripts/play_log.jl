using KiteModels, Serialization, ControlPlots, Dates, KiteViewers

kcu = KCU(se())
s = KPS4_3L(kcu)

set_data_path(joinpath(dirname(@__FILE__), "../logs/ars/KiteEnv-v3_66"))
# set_data_path(joinpath(dirname(@__FILE__), "../custom_envs/Environment/data"))

current_date = Dates.today()
# LOG_FILE_NAME = Dates.format(current_date, "dd-mm-yy")
LOG_FILE_NAME = "29-07-24"

println(LOG_FILE_NAME)
path = joinpath(get_data_path(), LOG_FILE_NAME) * ".arrow"
# logger = deserialize(path)
dt = 1/3
start_time = time()
TIME_LAPSE_RATIO = 1      # 1 = realtime, 2..8 faster
PARTICLES = 6*3 + 6         # 7 for tether and KCU, 4 for the kite
# end of user parameter section #

log=load_log(PARTICLES, LOG_FILE_NAME)
print(log.syslog)

viewer = Viewer3D(true)

function play(syslog)
    steps = length(syslog.time)
    start_time_ns = time_ns()
    KiteViewers.clear_viewer(viewer)
    for i in 1:steps
        if mod(i, TIME_LAPSE_RATIO) == 0 || i == steps
            update_system(viewer, syslog[i]; scale = 0.08, kite_scale=1.0)
            # save_png(viewer, index=div(i, TIME_LAPSE_RATIO))
            # wait_until(start_time_ns + dt*1e9, always_sleep=true)
            while time_ns() - start_time_ns < dt*1e9
                sleep(1e-9)
            end
            start_time_ns = time_ns()
        end
    end
end


play(log.syslog)
stop(viewer)
