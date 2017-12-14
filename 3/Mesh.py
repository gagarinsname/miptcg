from OpenGL.GL import *
import numpy as np

class Vertex(object):
    def __init__(self):
        self._x = 0.0
        self._y = 0.0
        self._z = 0.0
        self._nx = 0.0
        self._ny = 0.0
        self._nz = 0.0
        self._s = 0.0
        self._t = 0.0
        self._hasCoords = False
        self._hasNormal = False
        self._hasST = False

    def __str__(self):
        return "(x:{}, y:{}, z:{})".format(self._x, self._y, self._z)

    def setX(self, x):
        self._hasCoords = True
        self._x = x

    def setY(self, y):
        self._hasCoords = True
        self._y = y

    def setZ(self, z):
        self._hasCoords = True
        self._z = z

    def coords(self):
        return self._x, self._y, self._z

    def setNX(self, nx):
        self._hasNormal = True
        self._nx = nx

    def setNY(self, ny):
        self._hasNormal = True
        self._ny = ny

    def setNZ(self, nz):
        self._hasNormal = True
        self._nz = nz

    def addNX(self, nx):
        self._hasNormal = True
        self._nx += nx

    def addNY(self, ny):
        self._hasNormal = True
        self._ny += ny

    def addNZ(self, nz):
        self._hasNormal = True
        self._nz += nz

    def divideNormal(self, value):
        self._nx /= value
        self._ny /= value
        self._nz /= value

    def getNormal(self):
        return self._nx, self._ny, self._nz

    def setS(self, s):
        self._hasST = True
        self._s = s

    def setT(self, t):
        self._hasST = True
        self._t = t

    def stcoords(self):
        return self._s, self._t

    def hasCoords(self):
        return self._hasCoords

    def hasNormal(self):
        return self._hasNormal

    def hasST(self):
        return self._hasST

    def getNormal3f(self):
        if self._hasNormal:
            return self._nx, self._ny, self._nz
        else:
            return None


class Face(object):
    def __init__(self):
        self._vertices = []
        self._nx = 0
        self._ny = 0
        self._nz = 0

    def getNormal(self):
        return self._nx, self._ny, self._nz

    def set(self, l):
        self._vertices = l

    def vertices(self):
        return self._vertices

    def setNormal(self, normal3f):
        self._nx, self._ny, self._nz = normal3f


class Mesh(object):
    def __init__(self):
        self.vertices = []
        self.faces = list()
        self.pointData = list()
        self.colorData = list()
        self.edges = list()
        self.edgeNormals = list()

    def addVertex(self, v):
        self.vertices.append(v)

    def getVertex(self, vi):
        return self.vertices[vi]

    def addFace(self, f):
        self.faces.append(f)

    def calculateNormals(self):
        nVerticesPerFace = len(self.faces[0].vertices())

        for faceIndex in range(len(self.faces)):
            face = self.faces[faceIndex]
            normal3f = calcNormal(*(vertex.coords() for vertex in (self.getVertex(i) for i in face.vertices()[:3])))
            self.faces[faceIndex].setNormal(normal3f)
            vertexPairs = [set(elem) for elem in list(zip(face.vertices(), face.vertices()[1:]+[face.vertices()[0]]))]

            for vP in vertexPairs:
                if vP not in self.edges:
                    self.edges.append(vP)
                    self.edgeNormals.append(normal3f)
                else:
                    edgeIndex = self.edges.index(vP)
                    self.edgeNormals[edgeIndex] += normal3f
            nx, ny, nz = normal3f
            for i in face.vertices():
                self.vertices[i].addNX(nx)
                self.vertices[i].addNY(ny)
                self.vertices[i].addNZ(nz)

        for i in range(len(self.vertices)):
            self.vertices[i].divideNormal(nVerticesPerFace)

    def genPointData(self):
        for faceIndex in range(len(self.faces)):
            face = self.faces[faceIndex]

            for i in face.vertices():
                self.pointData.extend(self.vertices[i].coords())

        nTriangles = len(self.pointData)
        self.pointColor = [[0, 1, 1]] * 3 * nTriangles

    def draw(self, usedColor = (1.,1.,1.)):
        glCullFace(GL_BACK)
        glColor3f(*usedColor)
        mode = None
        for face in self.faces:
            numvertices = len(face.vertices())

            if numvertices == 3 and mode != GL_TRIANGLES:
                if mode:
                    glEnd()
                glBegin(GL_TRIANGLES)
                mode = GL_TRIANGLES

            elif numvertices == 4 and mode != GL_QUADS:
                if mode:
                    glEnd()
                glBegin(GL_QUADS)
                mode = GL_QUADS

            elif numvertices > 4:
                if mode:
                    glEnd()
                glBegin(GL_POLYGON)
                mode = GL_POLYGON

            elif numvertices < 3:
                raise RuntimeError('Face has <3 vertices')

            for vertex in [self.getVertex(i) for i in face.vertices()]:
                if vertex.hasNormal():
                    glNormal3f(*(vertex.getNormal()))
                glVertex3f(*(vertex.coords()))

            if mode == GL_POLYGON:
                glEnd()
                mode = None

        if mode:
            glEnd()

    def draw_silhouette(self, position3f, drawFaces=False, usedColor = (0.1, 9.0, 0.0)):
        mode = GL_LINES
        glLineWidth(10.0)
        glCullFace(GL_BACK)
        # glScale(1.02, 1.02, 1.02)
        glColor3f(*usedColor)
        cPosition = np.array(position3f)

        for i in range(len(self.edges)):
            if len(self.edgeNormals[i]) == 6:
                glBegin(mode)
                n1 = np.array(self.edgeNormals[i][:3])
                n2 = np.array(self.edgeNormals[i][3:])

                i1 = list(self.edges[i])[0]
                i2 = list(self.edges[i])[1]

                v1 = np.array(self.getVertex(i1).coords())
                v2 = np.array(self.getVertex(i2).coords())
                if np.dot(cPosition, n1) * np.dot(cPosition, n2) < 0:

                    glVertex3f(*tuple(v1))
                    glVertex3f(*tuple(v2))
                glEnd()

        if drawFaces:
            # glCullFace(GL_FRONT)
            glLineWidth(0.5)
            # glScale(0.99,0.99,0.99)
            glColor3f(0.1, 0.1, 0.5)
            # glColor4f(0.1, 0.1, 0.5)
            mode = None
            for face in self.faces:
                numvertices = len(face.vertices())

                if numvertices == 3 and mode != GL_TRIANGLES:
                    if mode:
                        glEnd()
                    glBegin(GL_TRIANGLES)
                    mode = GL_TRIANGLES

                elif numvertices == 4 and mode != GL_QUADS:
                    if mode:
                        glEnd()
                    glBegin(GL_QUADS)
                    mode = GL_QUADS

                elif numvertices > 4:
                    if mode:
                        glEnd()
                    glBegin(GL_POLYGON)
                    mode = GL_POLYGON

                elif numvertices < 3:
                    raise RuntimeError('Face has <3 vertices')

                for vertex in [self.getVertex(i) for i in face.vertices()]:
                    if vertex.hasNormal():
                        glNormal3f(*(vertex.getNormal()))
                    glVertex3f(*(vertex.coords()))

                if mode == GL_POLYGON:
                    glEnd()
                    mode = None

            if mode:
                glEnd()

            # glScale(0.98, 0.96, 0.98)
            # mode = None
            # for face in self.faces:
            #     numvertices = len(face.vertices())
            #
            #     if numvertices == 3 and mode != GL_TRIANGLES:
            #         if mode:
            #             glEnd()
            #         glBegin(GL_TRIANGLES)
            #         mode = GL_TRIANGLES
            #
            #     elif numvertices == 4 and mode != GL_QUADS:
            #         if mode:
            #             glEnd()
            #         glBegin(GL_QUADS)
            #         mode = GL_QUADS
            #
            #     elif numvertices > 4:
            #         if mode:
            #             glEnd()
            #         glBegin(GL_POLYGON)
            #         mode = GL_POLYGON
            #
            #     elif numvertices < 3:
            #         raise RuntimeError('Face has <3 vertices')
            #
            #     for vertex in [self.getVertex(i) for i in face.vertices()]:
            #         if vertex.hasNormal():
            #             glNormal3f(*(vertex.getNormal()))
            #         glVertex3f(*(vertex.coords()))
            #
            #     if mode == GL_POLYGON:
            #         glEnd()
            #         mode = None
            #
            # if mode:
            #     glEnd()

        glCullFace(GL_BACK)


    def draw_edges(self, usedColor = (0.0, 0.0, 0.0)):
        glLineWidth(1.0)
        mode = GL_LINES
        glColor3f(*usedColor)
        glBegin(mode)
        for face in self.faces:
            nVertices = len(face.vertices())
            for vertex in [self.getVertex(i) for i in face.vertices()]:
                glVertex3f(*(vertex.coords()))
            glVertex3f(*(self.getVertex(face.vertices()[0]).coords()))

        glEnd()

    def scale(self):
        massCenter = np.zeros(3)
        nVertices = len(self.vertices)
        for i in range(nVertices):
            massCenter += np.array(self.getVertex(i).coords())
        massCenter /= nVertices
        print(massCenter)
        for i in range(nVertices):
            cVertex = np.array(self.getVertex(i).coords())
            self.vertices[i].setX((cVertex[0] - massCenter[0]))
            self.vertices[i].setY((cVertex[1] - massCenter[1]))
            self.vertices[i].setZ((cVertex[2] - massCenter[2]))




def calcNormal(v1, v2, v3):
    a = np.array(v2, dtype='g') - np.array(v1, dtype='g')
    b = np.array(v3, dtype='g') - np.array(v1, dtype='g')
    n = np.cross(a,b)
    norm2 = np.linalg.norm(n)
    n /= norm2

    return n[0], n[1], n[2]

def dotProduct(a, b):
    if len(a) == len(b):
        return np.dot(np.array(a, dtype='g'), np.array(b, dtype='g'))
    else:
        return None
