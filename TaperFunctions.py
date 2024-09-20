from genesis.version4 import Genesis4, Write
import genesis.version4 as g4
import numpy as np

def parse_genesis4_lattice_file(filename, keys = ['Undulator', 'Quadrupole', 'Corrector', 'Phaseshifter', ' Drift', 'Chicane', 'Marker', 'Line']):
    """
    Parse genesis4 lattice file to an dictionary
    """


    with open(filename) as f:
        lines = f.readlines()
    output = {}
    for key in keys:
        output[key] = []

    ind = 0
    while ind  < len(lines):
        line = lines[ind]
        for key in keys:
            if key.upper() in line.upper() and '#' not in line:
                ele_str = line + ' '
                while '}' not in line:
                    ind += 1
                    line = lines[ind]
                    ele_str += line + ' '

                output[key].append(ele_str)
        ind += 1
    return output    


def gettaper(n_und, Kstart, dKbyK, ustart, ustop, order = 2):
    """
    Compute start and end K for each undulator section.
    order :  1 for linear taper, 2 for quadratic taper
    """
    Klist = []
    if ustart < n_und:
        print("apply taper ", n_und)
        for i in range(ustart):
            Klist.append([Kstart, Kstart])


        Kend = Kstart*(1-dKbyK)

        if ustop <n_und:
            fn = ustop
        else:
            fn = n_und
        nund_taper = fn- ustart

        if order == 1:
            Ktaper = np.linspace(Kstart, Kend, nund_taper + 1)
        elif order == 2:
            alpha = (Kend - Kstart)/nund_taper**2
            Ktaper = Kstart + alpha*np.arange(nund_taper + 1)**2

        for i in range(nund_taper):                                                                                                                           

            Klist.append([Ktaper[i], Ktaper[i + 1]])

        if ustop < n_und:
            for i in range(ustop, n_und):
                Klist.append([Kstart])


    else:
        for i in range(n_und):
            Klist.append([Kstart])
    
    return Klist


def write_constant_sec(usegname, K, nwig, uperiod):
    line = usegname + ': Undulator = {lambdau=' + str(uperiod) + ', nwig=' + str(nwig) + ', aw=' + str(K) + '};\n'
    return [line]


def write_linear_taper_sec(usegname, Kstart, Kend, nwig, uperiod):
    """
    Within an undulator, linearly change the taper of each period
    """
    Klist = np.linspace(Kstart, Kend, nwig)
    und_line = []
    ele_names = []
    for i in range(nwig):
        ele_name = usegname + str(i)
        line = usegname + str(i) + ': Undulator = {lambdau=' + str(uperiod) + ', nwig=1, aw=' + str(Klist[i]) + '};\n'
        und_line.append(line)
        ele_names.append(ele_name)
    return und_line, ele_names

def write_undulator(usegname_list, Kstart, dKbyK, ustart, ustop, nwig, uperiod, order = 2):

   
    Klist = gettaper(n_und = len(usegname_list), Kstart = Kstart, dKbyK = dKbyK, ustart = ustart, ustop = ustop, order = order)
   
    lines = []

    count = 0
    for Kpar in Klist:
        usegname = usegname_list[count]
        if len(Kpar) == 1:
            lines.extend(write_constant_sec(usegname, Kpar[0], nwig, uperiod))
        else:
            und_line, ele_names = write_linear_taper_sec(usegname+ '_s', Kpar[0], Kpar[1], nwig, uperiod)
            lines.extend(und_line)
            line = usegname + ': Line = {' + ele_names[0]
            for ele_name in ele_names[1:]:
                line += ', ' + ele_name
            line += '};\n'
            lines.append(line)
        count += 1
 #   print('I have lines')  
    return lines

def apply_taper(self, Kstart, dKbyK, ustart, ustop, nwig, uperiod, order = 2):
    """
    read from an existing lattice file and modifiying undulator
    """
  #  print('apply lattice')
    output_lines = []

    lattice=parse_genesis4_lattice_file(self.input.lattice.filename)

#    print(lattice)
    
    for key in lattice:
  #      print('key', key)
        if key != 'Undulator' and key != 'Line':
            
            output_lines.extend(lattice[key])
    
    usegname_list = []
    for und in lattice['Undulator']:
        usegname_list.append(und.split(':')[0])

 
    lines = write_undulator(usegname_list, Kstart, dKbyK, ustart, ustop, nwig, uperiod, order)
  #  print('lines', lines)
    output_lines.extend(lines)
    output_lines.extend(lattice['Line'])
   # print(outputlines)
#    self.input.lattice = output_lines
 #   self.input.lattice.filename =write_filename
    
 #   print('name', write_filename)
 #   with open(write_filename,'w') as tfile:
 #          print('writing file')
 #          tfile.write(''.join(output_lines))
    
   # print(output_lines)
    self.input.lattice=g4.Lattice.from_contents(''.join(output_lines))
