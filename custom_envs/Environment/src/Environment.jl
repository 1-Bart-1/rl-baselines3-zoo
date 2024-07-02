module Environment


using KiteModels, StaticArrays, LinearAlgebra, Serialization
export reset, step, render

const Model = KPS4_3L
kcu = nothing;
s = nothing;
dt = 1/se().sample_freq;
max_render_length = 10000;
i = 1;
logger = nothing;
integrator = nothing;
# integrator_history = load_history()
const StateVec = MVector{17, Float32}
state::StateVec = zeros(StateVec)
state_d::StateVec = zeros(StateVec)
state_dd::StateVec = zeros(StateVec)
last_state::StateVec = zeros(StateVec)
last_state_d::StateVec = zeros(StateVec)

function step(reel_out_speeds; prn=false)
    global i, sys_state, s, integrator
    reel_out_speeds = Vector{Float64}(reel_out_speeds)

    if prn
        KiteModels.next_step!(s, integrator, v_ro=reel_out_speeds, dt=dt)
    else
        redirect_stdout(devnull) do
            KiteModels.next_step!(s, integrator, v_ro=reel_out_speeds, dt=dt)
        end
    end
    
    i += 1
    return calc_state(s)
end

function reset(name="sim_log")
    global kcu, s, integrator, i, sys_state, logger, integrator_history

    if logger !== nothing
        name = String(name)
        path = joinpath(get_data_path(), name) * ".bin"
        for pos in logger
            println(pos[end])
        end
        serialize(path, logger)
    end
    
    update_settings()
    println(get_data_path())
    kcu = KCU(se());
    s = Model(kcu);
    @time logger = Vector{typeof(s.pos)}()
    integrator = KiteModels.init_sim!(s, stiffness_factor=0.04, prn=false, integrator_history=nothing)
    i = 1
    return calc_state(s)
end

function calc_state(s::KPS4_3L)
    global state, state_d, state_dd, last_state_d, last_state
    state .= vcat(
        s.l_tethers,                    # length 3
        normalize(s.pos[6]),            # length 3
        calc_orient_quat(s),            # length 4
        winch_force(s),                 # length 3
        calc_elevation(s),              # length 1
        calc_azimuth(s),                # length 1
        calc_heading(s),                # length 1
        calc_course(s)                  # length 1
    )
    state_d .= (state .- last_state) / 0.2
    state_dd .= (state_d .- last_state_d) / 0.2
    last_state_d .= state_d
    last_state .= state
    println("state\n", state)
    println("state_d\n", state_d)
    println("state_dd\n", state_dd)
    return vcat(state, state_d, state_dd)
end

function render()
    global sys_state, logger, i
    if(i <= max_render_length)
        push!(logger, deepcopy(s.pos))
    end
end

function close()
    # save_history(integrator_history)
end

end