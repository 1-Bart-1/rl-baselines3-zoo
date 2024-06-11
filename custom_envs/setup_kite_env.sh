echo "Creating .julia_sysimage.so..."
rm -f .julia_sysimage.so
julia -t 1 -e '
import Pkg;
Pkg.add("PythonCall");
Pkg.add("PackageCompiler");
Pkg.activate("Environment");
Pkg.update();
Pkg.instantiate();
using Environment;
using PackageCompiler;
create_sysimage(["Environment"], sysimage_path=".julia_sysimage.so", precompile_execution_file=".jl_precompile.jl");
'

# Check if .julia_sysimage.so was created successfully
if [ ! -f .julia_sysimage.so ]; then
    echo ".julia_sysimage.so was not created. Exiting..."
    exit 1
fi

python -c "
import os
os.environ['JULIA_NUM_THREADS'] = '1'
os.environ['PYTHON_JULIACALL_SYSIMAGE'] = os.path.join(os.getcwd(), '.julia_sysimage.so')
from juliacall import Main as jl
from time import time
jl.seval('using Pkg')
jl.Pkg.activate('Environment')
jl.seval('using Environment')

start = time()
jl.Environment.reset()
print('reset time', time() - start)

start = time()
jl.Environment.get_next_step(0, 0, 0)
print('step1 time', time() - start)

start = time()
jl.Environment.get_next_step(0, 0, 0)
print('step2 time', time() - start)

start = time()
jl.Environment.reset()
print('reset2 time', time() - start)
"