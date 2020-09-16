## Step 0 setup environmental variables for executable location ##

export QE_BIN="/home/dengtq/scratch/EPIC/q-e-qe-6.3-EPIC-public-test/bin/"
export BOLTZ_BIN="/home/dengtq/scratch/EPIC/boltztrap-EPIC-public-test/src/"
export SCRIPT_BIN="/home/dengtq/scratch/EPIC/script/"
export OMP_NUN_THREADS=1

## Step 1 SCF ##
cd phonon
mpirun -np 48 $QE_BIN/pw.x -nk 4 -inp scf.in 1> scf.out 2>> test.err

## Step 2 DFPT for dV_scf ##
mpirun -np 48 $QE_BIN/ph.x -nk 4 -inp  ph.in 1>  ph.out 2>> test.err

## Step 3 re-run SCF to include empty bands ##
mpirun -np 48 $QE_BIN/pw.x -nk 4 -inp scf.elph.in 1> scf.elph.out 2>> test.err

## Step 4 re-run ph.x to compute el-ph matrix elements and write to Si.epa.k ##
mpirun -np 48 $QE_BIN/ph.x -nk 4 -inp  ph.elph.in 1>  ph.elph.out 2>> test.err
cd ../

## Step 5.1 run NSCF calculation on denser k-grid ##
cd boltztrap
mpirun -np 48 $QE_BIN/pw.x -nk 4 -inp scf.in  1> scf.out  2>> test.err
mpirun -np 48 $QE_BIN/pw.x -nk 4 -inp nscf.in 1> nscf.out 2>> test.err

## Step 5.2 generate BoltzTraP input ##
$SCRIPT_BIN/qe2boltz-epic.py Si nscf.out

cd Si-boltz

## Step 6 run modified BoltzTraP ##
$BOLTZ_BIN/BoltzTraP BoltzTraP.def

## Step 7.1 soft-link files ##
cd ../

ln -fs ../phonon/Si.epa.k ./Si.epa.k
ln -fs ./Si-boltz/Si.curv     ./Si.curv
ln -fs ./Si-boltz/Si.sigxx    ./Si.sigxx
ln -fs ./Si-boltz/Si.transdos ./Si.transdos

## Step 7.2 run epic.x to compute generalized Eliashberg function ##
$QE_BIN/epic.x     < epic.in 1> epic.out 2>> test.err

## Step 8 run tau.epic.x to compute transport properties ##
$QE_BIN/tau.epic.x < tau.in  1> tau.out  2>> test.err

## Optionally: compute transport properties at specified carrier concentration ##
## $QE_BIN/tau.epic.x < tau.fixed_doping.in  1> tau.fixed_doping.out  2>> test.err
