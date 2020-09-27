# EPIC STAR

Energy-dependent Phonon- and Impurity- limited Carrier Scattering Time AppRoximation (EPIC STAR) is an approximation for Boltzmann transport properties simulation.

The theoretical and implementation details are described in:
Deng, T., Wu, G., Sullivan, M.B. et al. EPIC STAR: a reliable and efficient approach for phonon- and impurity-limited charge transport calculations. npj Comput Mater 6, 46 (2020). https://doi.org/10.1038/s41524-020-0316-7

Currently the code only works for three-dimensional systems, and care should be taken in special cases, such as those extreme anisotropy, soft phonons, or flat bands.

Knowledge of Quantum Espresso (especially ph.x) and BoltzTraP is needed, and please consult their manuals for input explanation.

## Installation

Apply the corresponding patches for BoltzTraP and QE and compile as usual.

BoltzTraP:
1. Download and unpack BoltzTraP 1.2.5 as boltztrap-1.2.5
	tar -jxvf boltztrap-1.2.5.tar.bz2
2. Apply patch
	patch -p0 < ./epicstar/src/boltztrap-1.2.5-EPIC.patch
3. Configure and compile BoltzTraP as usual

QE 6.3:
1. Download and unpack QE 6.3 as q-e-qe-6.3
	tar -zxvf q-e-qe-6.3.tar.gz
2. Apply patch
	patch -p0 < ./epicstar/src/qe-6.3-EPIC.patch
3. Configure and compile ph as usual

## Workflow

1. Run SCF calculation using pw.x ('fixed' occupation is needed for polar correction).

2. Run DFPT calculation using ph.x to obtain dV\_scf (phonon perturbation potential).

   2. 1. optional: run frohlich.x with lfroh = .true. to obtain Frohlich interaction strength file prefix.dyn1.froh.
      This requires running ph.x with 'fixed' occupation and epsil = .true., and q=0 Gamma point should be the first q-point.

3. Re-run SCF calculation using pw.x with sufficient empty bands in order to compute el-ph matrix for conduction bands.

4. Run DFPT calculation with trans = .false. and electron\_phonon = 'epa' to obtain el-ph matrix elements file (prefix.epa.k).

5. Run NSCF calculation on a denser k-grid to obtain band structure needed by BoltzTraP. Then use qe2boltz-epic.py to generated BoltzTraP input.

6. Run modified BoltzTraP program for prefix.transdos, prefix.sigxx, and prefix.curv.

7. Run epic.x to compute the generalized Eliashberg function which describes the short-range el-ph interaction.

8. Run tau.epic.x to compute transport properties at arbitrary condition (temperature, doping, etc.).

### Input file for epic.x, frohlich.x and tau.epic.x

#### epic.x

The input for **epic.x** is rather similar to epa.x, as it reads the epa.k file originally generated for EPA.

| Lines                       | Description                                                        |
|-----------------------------|--------------------------------------------------------------------|
| `Si.epa.k`                  | epa.k file produced by ph.x with electron\_phonon = 'epa'          |
| `Si`                        | prefix for output files, including generalized Eliashberg function |
| `epic`                      | job type. Currently only 'epic' is used.                           |
| `6.2586 -0.0027211 200 1 4` | VBM, dE\_v, N\_E\_v, nbnd\_min\_v, nbnd\_max\_v                    |
| `6.6992  0.0027211 200 5 8` | CBM, dE\_c, N\_E\_c, nbnd\_min\_c, nbnd\_max\_c                    |
| `0.2 0.005`                 | Electron and phonon smearing paramters in eV                       |

For line 4 and 5:
| Symbol                                               | Explanation                                                                               |
|------------------------------------------------------|-------------------------------------------------------------------------------------------|
| VBM(CBM)                                             | valence (conduction) band edge energy in eV                                               |
|dE\_v(dE\_c)                                          | valence (conduction) band energy sampling step in eV, for generalized Eliashberg function |
|N\_E\_v(N\_E\_c)                                      | number of energy sampling points for valence (conduction) band                            |
|nbnd\_min\_v,nbnd\_max\_v(nbnd\_min\_c, nbnd\_max\_c) | min and max indices of valence (conduction) bands to include                              |

#### frohlich.x

The input file for frohlich.x is largely identical to dynmat.x of QE. Only the following two optionas are added:

| Options | Description                                                                                                                         |
|---------|-------------------------------------------------------------------------------------------------------------------------------------|
| lfroh   | .true. to compute Frohlich interaction strength. If .false. frohlich.x is identical to dynmat.x                                     |
| nmesh   | number of angular sampling point for numerical integration, needed to compute spherically averaged Frohlich interaction strength    |

#### tau.epic.x

The input for **tau.epic.x**:

| Lines             | Description                                                                                                                         |
|-------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| `Si`              | prefix, same as QE, BoltzTraP and epic.x                                                                                            |
| `2`               | spin degeneracy (2 for nspin = 1, 1 for nspin = 2)                                                                                  |
| `300`             | temperature in K                                                                                                                    |
| `6.5 6.51`        | lowest and highest chemical potential (Fermi level) in eV                                                                           |
| `2`               | number of chemical potential to sample. Optional: an extra number to define a desired carrier density in m^-3 (positive for n-dope) |
| `imp`             | scattering mechanisms: `eph` for el-ph only, `tf-eph` for Thomas-Fermi screened el-ph, `imp` for TF-screened el-ph + el-imp         |
| `39.14770475`     | unit-cell volume in Ang^3                                                                                                           |
| ``                | filename of .froh file generated by frohlich.x. Leave blank to neglect Frohlich correction.                                         |
| `0.0 14.323856554`| Impurity density and averaged dielectric constant. If impurity density is zero, n_imp == abs(n_doping)                              |

Note if .froh file is provided, averaged dielectric constant is read from .froh and overwrite the option here.

If desired carrier density is provided in line 5 after number of chemical potential sample, one single chemical potential corresponding to this density is used.

### Output files

epic.x is used to generate the following files:

prefix.epic.g2:    containing generalized Eliashberg function
prefix.epic.invq2: containing information for Frohlich correction

tau.epic.x is used to generate the following files:

prefix.{data}.dat:   containing transport data (conductivity sigma, mobility, Seebeck coefficient, power factor PF etc.)
prefix.e.{data}.dat: same as above, with only conduction band contribution
prefix.h.{data}.dat: same as above, with only valence band contribution

## Examples

Simple examples for silicon and gallium arsenide are provided. See their respective test.sh for details.

## Licenses

Patches to Quantum ESPRESSO and BoltzTraP are distributed under GPL-2.0 and LGPL-3.0+ licenses, respectively.
