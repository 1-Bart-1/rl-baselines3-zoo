using KiteViewers, KiteUtils

# kcu = KCU(se())
# s = KPS4_3L(kcu)

set_data_path(joinpath(dirname(@__FILE__), "../logs/ars/KiteEnv-v3_132"))
try
    cp(joinpath(dirname(@__FILE__), "../custom_envs/Environment/data/settings.yaml"), joinpath(get_data_path(),"settings.yaml"))
    cp(joinpath(dirname(@__FILE__), "../custom_envs/Environment/data/system.yaml"), joinpath(get_data_path(),"system.yaml"))
catch
end

LOG_FILE_NAME = "render"

dt = 1/20
start_time = time()
TIME_LAPSE_RATIO = 1      # 1 = realtime, 2..8 faster
PARTICLES = 6*3 + 6         # 7 for tether and KCU, 4 for the kite
# end of user parameter section #

println("loading log...")
log=load_log(LOG_FILE_NAME; path=get_data_path())
# print(log.syslog)

viewer = Viewer3D(true)
println("playing log...")
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
