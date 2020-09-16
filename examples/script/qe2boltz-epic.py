#! /bin/env python
import os
import numpy as np

eps3 = 1.0e-3
inf6 = 1.0e6
rydberg = 13.605691930242389083319508233427

def main(argv = None):
    if argv is None:
        argv = sys.argv
    if len(argv) < 3 or len(argv) > 4:
        self = '/' + argv[0]
        self = self[len(self)-self[::-1].find('/'):]
        print("")
        print("    Converts the output of Quantum Espresso")
        print("    to the input of BoltzTraP")
        print("")
        print("    Usage: %s prefix nscf.out [nbnd_exclude]")
        print("")
        print("  * prefix = name of the system, same as in espresso input file")
        print("  * nscf.out = name of the nscf calculation output file")
        print("  * nbnd_exclude = number of the lowest energy bands to exclude in the output")
        print("")
        return 1

    prefix = argv[1]
    fname_pw = argv[2]
    if len(argv) > 3:
        nbnd_exclude = int(argv[3])
    else:
        nbnd_exclude = 0

    cwd = os.getcwd()
    dir_boltz = cwd+'/'+prefix+'-boltz'
    os.system('mkdir '+prefix+'-boltz')
    fname_def = 'BoltzTraP.def'
    fname_intrans = prefix + '.intrans'
    fname_struct = prefix + '.struct'

    deltae = 0.0002
    ecut = 0.2
    lpfac = 5
    efcut = 0.15
    tmax = 300.0
    deltat = 300.0
    ecut2 = -1.0
    dosmethod = 'TETRA'

    f = open(fname_pw, 'r')
    f_pw = f.readlines()
    f.close()

    i = 0
    efermi_scf = (inf6 + eps3) / rydberg
    avec = []
    idxsym = []
    nsym = 1
    idxbnd = []
    spin = False
    for line in f_pw:
        if 'lattice parameter (alat)  =' in line:
            alat = float(line.split()[4])
        elif ' a(' in line:
            atext = line[23:57].split()
            avec.append([float(atext[0]) * alat, float(atext[1]) * alat, float(atext[2]) * alat])
        elif 'cryst.   s' in line:
            idxsym.append(i)
        elif 'the Fermi energy is' in line:
            efermi_scf = float(line.split()[4]) / rydberg
        elif 'the spin up/dw Fermi energies are' in line:
            efermi_scf = (float(line.split()[6]) + float(line.split()[7])) / (2.0 * rydberg)
        elif 'highest occupied, lowest unoccupied level' in line:
            efermi_scf = (float(line.split()[6]) + float(line.split()[7])) / (2.0 * rydberg)
        elif 'number of electrons' in line:
            nelec = float(line.split()[4])
        elif 'Sym.Ops.' in line or 'Sym. Ops.' in line:
            nsym = int(line.split()[0])
        elif 'number of k points=' in line:
            nkpt = int(line.split()[4])
        elif 'number of Kohn-Sham states=' in line:
            nbnd = int(line.split()[4])
        elif ' cryst. coord.' in line:
            idxkpt = i + 1
        elif 'band energies (ev)' in line or 'bands (ev)' in line:
            idxbnd.append(i + 2)
        elif 'SPIN' in line:
            spin = True
        i += 1

    efermi = efermi_scf

    if spin:
        nelec -= nbnd_exclude
        fname_energy = prefix + '.energyso'
    else:
        nelec -= 2 * nbnd_exclude
        fname_energy = prefix + '.energy'

    rot = []
    for ir in range(nsym):
        rot.append([])
        for i in range(3):
            rtext = f_pw[idxsym[ir] + i][19:53].split()
            rot[ir].append([int(rtext[0]), int(rtext[1]), int(rtext[2])])

    kpoint = []
    for ik in range(nkpt):
        ktext = f_pw[idxkpt + ik][20:56].split()
        kpoint.append([float(ktext[0]), float(ktext[1]), float(ktext[2])])

    energy = []
    ncol = 8
    nrow = nbnd // ncol
    if nbnd % ncol != 0:
        nrow += 1
    if spin:
        nkpt_tot = nkpt*2
    else:
        nkpt_tot = nkpt
    for ik in range(nkpt_tot):
        energy.append([])
        nelem = ncol
        for ir in range(int(nrow)):
            etext = f_pw[idxbnd[ik] + ir].split()
            if ir == nrow - 1:
                nelem = nbnd - ncol * (nrow - 1)
            for ie in range(nelem):
                energy[ik].append(float(etext[ie]) / rydberg)

    os.chdir(dir_boltz)

    f_def = '5, \'' + prefix + '.intrans\',      \'old\',    \'formatted\',0\n'
    f_def += '6,\'' + prefix + '.outputtrans\',      \'unknown\',    \'formatted\',0\n'
    f_def += '20,\'' + prefix + '.struct\',         \'old\',    \'formatted\',0\n'
    f_def += '10,\'' + fname_energy + '\',         \'old\',    \'formatted\',0\n'
    f_def += '48,\'' + prefix + '.engre\',         \'unknown\',    \'unformatted\',0\n'
    f_def += '49,\'' + prefix + '.transdos\',        \'unknown\',    \'formatted\',0\n'
    f_def += '50,\'' + prefix + '.sigxx\',        \'unknown\',    \'formatted\',0\n'
    f_def += '51,\'' + prefix + '.sigxxx\',        \'unknown\',    \'formatted\',0\n'
    f_def += '152,\'' + prefix + '.v2dos\',        \'unknown\',    \'formatted\',0\n'
    f_def += '153,\'' + prefix + '.curv\',        \'unknown\',    \'formatted\',0\n'
    f_def += '154,\'' + prefix + '.mm1\',        \'unknown\',    \'formatted\',0\n'

    f = open(fname_def, 'w')
    f.write(f_def)
    f.close()

    f_intrans = 'GENE                      # Format of DOS\n'
    f_intrans += '0 1 0 0.0                 # iskip (not presently used) idebug setgap shiftgap\n'
    f_intrans += str(efermi) + ' ' + str(deltae) + ' ' + str(ecut) + ' ' + str(nelec) + '    # Fermilevel (Ry), energygrid, energy span around Fermilevel, number of electrons\n'
    f_intrans += 'CALC                      # CALC (calculate expansion coeff), NOCALC read from file\n'
    f_intrans += str(lpfac) + '                         # lpfac, number of latt-points per k-point\n'
    f_intrans += 'BOLTZ                     # run mode (only BOLTZ is supported)\n'
    f_intrans += str(efcut) + '                      # (efcut) energy range of chemical potential\n'
    f_intrans += str(tmax) + ' ' + str(deltat) + '                # Tmax, temperature grid\n'
    f_intrans += str(ecut2) + '                      # energyrange of bands given individual DOS output sig_xxx and dos_xxx (xxx is band number)\n'
    f_intrans += dosmethod + '\n'

    f = open(fname_intrans, 'w')
    f.write(f_intrans)
    f.close()

    f_energy = prefix + '\n'
    f_energy += str(nkpt) + '\n'
    if spin:
        for ik in range(nkpt):
            f_energy += str(kpoint[ik][0]) + ' ' + str(kpoint[ik][1]) + ' ' + str(kpoint[ik][2]) + ' ' + str(nbnd*2 - nbnd_exclude*2) + '\n'
            sort_energy = np.sort(np.array(energy[ik]+energy[ik+nkpt],dtype=np.float))
            for ib in range(nbnd_exclude*2, nbnd*2):
                f_energy += str(sort_energy[ib]) + '\n'
    else:
        for ik in range(nkpt):
            f_energy += str(kpoint[ik][0]) + ' ' + str(kpoint[ik][1]) + ' ' + str(kpoint[ik][2]) + ' ' + str(nbnd - nbnd_exclude) + '\n'
            for ib in range(nbnd_exclude, nbnd):
                f_energy += str(energy[ik][ib]) + '\n'

    f = open(fname_energy, 'w')
    f.write(f_energy)
    f.close()

    f_struct = prefix + '\n'
    for i in range(3):
        f_struct += str(avec[i][0]) + ' ' + str(avec[i][1]) + ' ' + str(avec[i][2]) + '\n'
    f_struct += str(nsym) + '\n'
    for ir in range(nsym):
        f_struct += str(rot[ir][0][0]) + ' ' + str(rot[ir][1][0]) + ' ' + str(rot[ir][2][0]) + ' '
        f_struct += str(rot[ir][0][1]) + ' ' + str(rot[ir][1][1]) + ' ' + str(rot[ir][2][1]) + ' '
        f_struct += str(rot[ir][0][2]) + ' ' + str(rot[ir][1][2]) + ' ' + str(rot[ir][2][2]) + '\n'

    f = open(fname_struct, 'w')
    f.write(f_struct)
    f.close()

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
