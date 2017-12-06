from Mesh import Mesh, Vertex, Face
import re
import numpy as np

def get_float(cstr):
    return float(cstr)


def get_float32(cstr):
    return np.float32(cstr)


def get_double(cstr):
    return float(cstr)


def get_char(cstr):
    return int(cstr)


def get_uchar(cstr):
    return int(cstr)


def get_short(cstr):
    return int(cstr)


def get_ushort(cstr):
    return int(cstr)


def get_int(cstr):
    return int(cstr)

def get_uint(cstr):
    return int(cstr)


def get_uint8(cstr):
    return np.uint8(cstr)


def parse_ply(fname):
    m = Mesh()
    state = 'init'
    format_re = re.compile('format\\s+ascii\\s+1.0')
    comment_re = re.compile('comment\\s.*')
    element_re = re.compile('element\\s+(?P<name>\\w+)\\s+(?P<num>\\d+)')
    property_re = re.compile('property\\s+(?P<type>\\w+)\\s+(?P<name>\\w+)')
    property_list_re = re.compile('property\\s+list\\s+(?P<itype>\\w+)\\s+(?P<etype>\\w+)\\s+(?P<name>\\w+)')
    element_types = []
    vertex_names = {
        'x': lambda v, x: v.setX(x),
        'y': lambda v, y: v.setY(y),
        'z': lambda v, z: v.setZ(z),
        'nx': lambda v, nx: v.setNX(nx),
        'ny': lambda v, ny: v.setNY(ny),
        'nz': lambda v, nz: v.setNZ(nz),
        's': lambda v, s: v.setS(s),
        't': lambda v, t: v.setT(t)
    }
    face_names = {
        #'vertex_indices': (lambda f, l, m=m: f.set([m.getVertex(v) for v in l])) #real values of vertices
        'vertex_indices': (lambda f, l, m=m: f.set(l))                            #references to vertices
    }
    element_type_dict = {
        'vertex' : (lambda: Vertex(), vertex_names, lambda v, m=m: m.addVertex(v)),
        'face' : (lambda: Face(), face_names, lambda f, m=m: m.addFace(f))
    }
    type_handles = {
         'float': get_float,
        'float32': get_float32,
        'double': get_double,
          'char': get_char,
         'uchar': get_uchar,
         'short': get_short,
        'ushort': get_ushort,
           'int': get_int,
         'int32': get_int,
          'uint': get_uint,
         'uint8': get_uint8
    }
    i = j = 0
    for line in open(fname, 'r'):
        line = line.rstrip()
        if state == 'init':
            if line != 'ply':
                raise RuntimeError('PLY: file is not a ply file')
            state = 'format'
        elif state == 'format':
            if not format_re.match(line):
                raise RuntimeError('PLY: unsupported ply format')
            state = 'header'
        elif state == 'header':
            if comment_re.match(line):
                #comment, do nothing
                continue
            match = element_re.match(line)
            if match:
                element_types.append((match.group('name'), int(match.group('num')), []))
                continue
            match = property_list_re.match(line)
            if match:
                element_types[-1][2].append((match.group('name'), 'list', match.group('itype'), match.group('etype')))
                continue
            match = property_re.match(line)
            if match:
                element_types[-1][2].append((match.group('name'), match.group('type')))
                continue
            if line == 'end_header':
                state = 'body'
                continue
            raise RuntimeError('PLY: unknown header field')
        elif state == 'body':
            if j >= element_types[i][1]:
                j = 0
                i = i + 1

            if i >= len(element_types):
                raise RuntimeExeception('PLY: too much data in file')

            line = line.split()
            actions = element_type_dict[element_types[i][0]]
            obj = actions[0]()

            for propty in element_types[i][2]:
                x = None
                if propty[1] == 'list':
                    numelems = type_handles[propty[2]](line[0])
                    line = line[1:]
                    x = []
                    for count in range(numelems):
                        x.append(type_handles[propty[3]](line[0]))
                        line = line[1:]
                else:
                    x = type_handles[propty[1]](line[0])
                    line = line[1:]
                actions[1][propty[0]](obj, x)
            actions[2](obj)
            j = j + 1

    m.calculateNormals()
    return m

def register(handlers):
    handlers['ply'] = parse_ply