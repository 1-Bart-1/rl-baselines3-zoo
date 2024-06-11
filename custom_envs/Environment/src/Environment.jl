module Environment


using KiteModels
export reset, get_next_step

const Model = KPS4
kcu = nothing;
kps4 = nothing;
dt = 1/se().sample_freq;
steps = 10000;
step = 0;
logger = nothing;
integrator = nothing;
# integrator_history = load_history()

function get_next_step(depower, steering, v_reel_out)
    global step, sys_state, kps4, integrator
    depower = Float32(depower)
    steering = Float32(steering)
    v_reel_out = Float32(v_reel_out)

    set_depower_steering(kps4.kcu, depower, steering)

    redirect_stdout(devnull) do
        KiteModels.next_step!(kps4, integrator, v_ro=v_reel_out, dt=dt)
    end
    
    sys_state = SysState(kps4)
    step += 1
    return sys_state.orient[1], sys_state.orient[2], sys_state.orient[3], sys_state.orient[4], sys_state.force, sys_state.elevation, sys_state.azimuth, sys_state.l_tether, sys_state.heading
end

function reset(name="sim_log")
    global kcu, kps4, integrator, step, sys_state, logger, integrator_history

    if logger !== nothing
        name = String(name) #not in the sysimage yet
        save_log(logger, name)
    end
    logger = Logger(se().segments + 5, steps)
    
    update_settings()
    kcu = KCU(se());
    kps4 = Model(kcu);
    integrator = KiteModels.init_sim!(kps4, stiffness_factor=0.04, prn=false, integrator_history=nothing) # should pass integrator_history object to this
    step = 0
    sys_state = SysState(kps4)
    return sys_state.orient[1], sys_state.orient[2], sys_state.orient[3], sys_state.orient[4], sys_state.force, sys_state.elevation, sys_state.azimuth, sys_state.l_tether, sys_state.heading
end

function render()
    global sys_state, logger, step
    if(step < steps)
        log!(logger, sys_state)
    end
end

function close()
    # save_history(integrator_history)
end

end