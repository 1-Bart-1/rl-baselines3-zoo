module Environment

using KiteModels, KiteModels.StaticArrays, KiteModels.LinearAlgebra, KiteModels.Parameters
import KiteModels.OrdinaryDiffEqCore: ODEIntegrator
export reset, step, render, Env

const StateVec = MVector{15, Float32}

@with_kw mutable struct Env
    kcu::KCU = KCU(se("system.yaml"))
    s::KPS4_3L = KPS4_3L(kcu)
    max_render_length::Int = 10000
    i::Int = 1
    logger::Logger = Logger(s.num_A, max_render_length)
    sys_state::Union{Nothing, SysState} = nothing
    state::StateVec = zeros(StateVec)
    state_d::StateVec = zeros(StateVec)
    state_dd::StateVec = zeros(StateVec)
    last_state::StateVec = zeros(StateVec)
    last_state_d::StateVec = zeros(StateVec)
    wanted_elevation::Float32 = 0.0
    wanted_azimuth::Float32 = 0.0
    min_tether_length::Float32 = 0.0
    max_force::Float32 = 0.0
    heading::Float32 = 0.0
end

function step(e::Env, reel_out_torques; prn=false)
    e.i += 1
    reel_out_torques = Vector{Float32}(reel_out_torques) * 100
    old_heading = calc_heading(e.s)
    if prn
        KiteModels.next_step!(e.s; set_values=reel_out_torques)
    else
        redirect_stderr(devnull) do
            redirect_stdout(devnull) do
                KiteModels.next_step!(e.s; set_values=reel_out_torques)
            end
        end
    end
    _calc_heading(e, old_heading, calc_heading(e.s))
    _update_objective!(e)
    return (false, _calc_state(e, e.s))
end

function reset(e::Env, name="sim_log")
    if length(e.logger) > 1
        name = String(name)
        save_log(e.logger, basename(name))
    end
    
    e.wanted_elevation = deg2rad(85)
    e.wanted_azimuth = 0.0
    e.min_tether_length = e.s.set.l_tether
    e.max_force = 5000.0
    e.heading = 0.0
    update_settings()
    e.i = 0
    KiteModels.init_sim!(e.s; prn=false, torque_control=true)
    return _calc_state(e, e.s)
end

function render(e::Env)
    if (e.i == 1)
        e.logger = Logger(e.s.num_A, e.max_render_length)
        e.sys_state = SysState(e.s)
    end
    if (e.i <= e.max_render_length)
        update_sys_state!(e.sys_state, e.s)
        log!(e.logger, e.sys_state)
    end
    return nothing
end

function _calc_state(e::Env, s::KPS4_3L)
    e.state .= vcat(
        _calc_reward(e,s),                # length 1
        calc_orient_quat(s),            # length 4
        s.tether_lengths / 100.0,                    # length 3 # normalize to min and max 
        KiteModels.calc_elevation(s) / (0.5π),       # length 1
        KiteModels.calc_azimuth(s) / (0.5π),         # length 1
        sum(winch_force(s)) / 10000,            # length 1
        e.wanted_elevation / (0.5π),                # length 1
        e.wanted_azimuth / (0.5π),               # length 1
        e.min_tether_length / 100.0,            # length 1
        e.max_force / 10000                     # length 1
    )
    # if e.i == 0
    #     e.state_d .= zeros(StateVec)
    # else
    #     e.state_d .= (e.state .- e.last_state) / e.s.set.sample_freq
    # end
    # if e.i <= 1
    #     e.state_dd .= zeros(StateVec)
    # else
    #     e.state_dd .= (e.state_d .- e.last_state_d) / e.s.set.sample_freq
    # end
    # e.last_state_d .= e.state_d
    # e.last_state .= e.state
    # return vcat(e.state, e.state_d, e.state_dd)
    return e.state
end

function _calc_reward(e::Env, s::KPS4_3L)
    if  any(abs.(s.flap_angle) .>= deg2rad(40)) ||
        !(-2π < e.heading < 2π) ||
        s.tether_lengths[3] < e.min_tether_length ||
        s.tether_lengths[3] > e.min_tether_length*1.5 ||
        sum(winch_force(s)) > e.max_force
        return 0.1
    end
    range = deg2rad(5)
    elevation_reward = max(0.0, range - abs(e.wanted_elevation - KiteModels.calc_elevation(s))) / range
    azimuth_reward   = max(0.0, range - abs(e.wanted_azimuth - KiteModels.calc_azimuth(s))) / range
    return elevation_reward + azimuth_reward + 0.5 # IMPORTANT: HAS TO BE POSTITIVE, >0
end

function _update_objective!(e::Env)
    t = e.i / e.s.set.sample_freq
    period = 40.0
    amplitude = deg2rad(30.0)
    e.wanted_azimuth = amplitude * sin(2π * t / period)
    e.wanted_elevation = e.wanted_elevation
    nothing
end

# function _calc_force_component(e::Env, s::KPS4_3L)
#     wanted_force_vector = [cos(e.wanted_elevation)*cos(e.wanted_azimuth), cos(e.wanted_elevation)*-sin(e.wanted_azimuth), sin(e.wanted_elevation)]
#     tether_force = sum(s.winch_forces)
#     force_component = tether_force ⋅ wanted_force_vector
#     return force_component
# end

function _calc_heading(e::Env, old_heading, new_heading)
    d_heading = new_heading - old_heading
    if d_heading > 1
        d_heading -= 2π
    elseif d_heading < -1
        d_heading += 2π
    end
    e.heading += d_heading
    return nothing
end

end