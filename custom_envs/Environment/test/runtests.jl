using Revise, Test
using Environment

@testset "Environment test" begin
    e = Env()
    reset_float = Environment.reset(e)
    @test all(-1.0 .<= reset_float .<= 1.0)
    (_, step_float) = Environment.step(e, [0,0,0])
    @test !all(step_float .≈ reset_float)
    @test all(-1.0 .<= step_float .<= 1.0)
    Environment.render(e)
    (_, step2_float) = Environment.step(e, [0,0,0])
    @test !all(step2_float .≈ reset_float)
    @test !all(step2_float .≈ step_float)
    @test all(-1.0 .<= step2_float .<= 1.0)
    Environment.render(e)
    reset2_float = Environment.reset(e)
    @show reset_float
    @show reset2_float
    @test all(reset2_float .≈ reset_float)
    @test all(-1.0 .<= reset2_float .<= 1.0)
    @test length(reset2_float) == length(step_float)
    @show length(reset2_float)
end