import sys
import os
import importlib
import matrices
import numpy as np

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import argparse

import filetypes
handlers = {}
for m in filetypes.__all__:
    importlib.import_module('filetypes.'+m).register(handlers)

import Mesh
global mesh
mesh = None

scaleFactor = 1.2
rotateFactor = 0.2
translateFactor = 0.05
brightLightPosition4f = (0.0, 20.0, 100.0, 0)
dimLightPosition4f = (-10, -10, -10, 0)
initialPosition = matrices.Vector4d(0, 3, 10, 1)


# Gets called by glutMainLoop() many times per second
def doIdle():    
    pass    # Remove if we actually use this function


def doKeyboard(*args):
    global cameraMatrix
    if args[0] == '+':
        cameraMatrix = cameraMatrix * matrices.scale(1 / scaleFactor, 1 / scaleFactor, 1 / scaleFactor)
    elif args[0] == '-':
        cameraMatrix = cameraMatrix * matrices.scale(scaleFactor, scaleFactor, scaleFactor)
    elif args[0] == 'q':
        cameraMatrix = cameraMatrix * matrices.rotateZ(-rotateFactor)
    elif args[0] == 'e':
        cameraMatrix = cameraMatrix * matrices.rotateZ(rotateFactor)
    elif args[0] == '0':
        cameraMatrix = matrices.getIdentity4x4()
    else:
        return
    doRedraw()


def click( button, state, x, y ):
    """Handler for click on the screen"""
    global cameraMatrix
    # Hard-coded mouse scroll buttons: suits for my laptop Lenovo G570 and
    if button == 3 and state == GLUT_DOWN:
        cameraMatrix = cameraMatrix * matrices.scale(1 / scaleFactor, 1 / scaleFactor, 1 / scaleFactor)
    elif button == 4 and state == GLUT_DOWN:
        cameraMatrix = cameraMatrix * matrices.scale(scaleFactor, scaleFactor, scaleFactor)
    elif button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        cameraMatrix = cameraMatrix * matrices.rotateZ(-rotateFactor)
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        cameraMatrix = cameraMatrix * matrices.rotateZ(rotateFactor)
    doRedraw()


def doSpecial(*args):
    global cameraMatrix
    glutMouseFunc(click)
    if glutGetModifiers() & GLUT_ACTIVE_SHIFT:
        if args[0] == GLUT_KEY_UP:
            cameraMatrix = cameraMatrix*matrices.translate(0, -translateFactor, 0)  # MOVE UP
        if args[0] == GLUT_KEY_DOWN:
            cameraMatrix = cameraMatrix*matrices.translate(0, translateFactor, 0)   # MOVE DOWN
        if args[0] == GLUT_KEY_LEFT:
            cameraMatrix = cameraMatrix*matrices.translate(translateFactor, 0, 0)   # MOVE LEFT
        if args[0] == GLUT_KEY_RIGHT:
            cameraMatrix = cameraMatrix*matrices.translate(-translateFactor, 0, 0)  # MOVE RIGHT
    else:
        if args[0] == GLUT_KEY_UP:
            cameraMatrix = cameraMatrix*matrices.rotateX(-rotateFactor)             # ROTATE UP
        if args[0] == GLUT_KEY_DOWN:
            cameraMatrix = cameraMatrix*matrices.rotateX(rotateFactor)              # ROTATE DOWN
        if args[0] == GLUT_KEY_LEFT:
            cameraMatrix = cameraMatrix*matrices.rotateY(-rotateFactor)             # ROTATE LEFT
        if args[0] == GLUT_KEY_RIGHT:
            cameraMatrix = cameraMatrix*matrices.rotateY(rotateFactor)              # ROTATE RIGHT
    doRedraw()


# Called by glutMainLoop() when window is resized
def doReshape(width, height):
    global cameraMatrix
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glViewport(0, 0, width, height)
    gluPerspective(30.0, (float(width)) / height, .01, 100)

    doCamera()


def doCamera():

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    orientationMatrix = cameraMatrix.copy()
    orientationMatrix[3] = matrices.Vector4d(0, 0, 0, 1)
    pos = initialPosition * cameraMatrix
    lookAt = matrices.Vector4d(0, 0, 0, 1) * cameraMatrix
    direction = matrices.Vector4d(0, 1, 0, 1) * orientationMatrix
    gluLookAt(*(pos.list()[:-1] + lookAt.list()[:-1] + direction.list()[:-1]))


# Called by glutMainLoop() when screen needs to be redrawn
def doRedraw():
    doCamera()
    global cameraMatrix
    global args

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # glMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE, (.25, .25, .25, 1.0))
    glMaterial(GL_FRONT, GL_SPECULAR, (1.0, 1.0, 1.0, .5))
    glMaterial(GL_FRONT, GL_SHININESS, (128.0, ))

    # glMaterial(GL_BACK, GL_AMBIENT_AND_DIFFUSE, (0., 0., 0., 0.))
    # glMaterial(GL_FRONT, GL_SPECULAR, (0., 0., 0., 0.))
    # glMaterial(GL_FRONT, GL_SHININESS, (0.,))

    if args.silhouette:
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        mv = glGetDoublev(GL_MODELVIEW_MATRIX)
        position = mv[:-1, 2]
        orientationMatrix = cameraMatrix.copy()
        orientationMatrix[3] = matrices.Vector4d(0, 0, 0, 1)
        lookAt = matrices.Vector4d(0, 1, 0, 1) * orientationMatrix
        position = position# + np.array(lookAt.list()[:-1])
        mesh.draw_silhouette(position) # , ~args.faces)
        glPopMatrix()
    if args.edges:
        edgeColor = (0.1, 0.5, 0.1)
        glLineWidth(3.0)
        mesh.draw_edges(edgeColor)
    if args.faces:
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        meshColor = (0.4, 0.5, 0.1)
        mesh.draw(meshColor)
        glPopMatrix()
    glutSwapBuffers()  # Draws the new image to the screen if using double buffers


def doRedrawShader():
    pass

if __name__ == '__main__':
    global cameraMatrix
    global args
    cameraMatrix = matrices.getIdentity4x4()

    parser = argparse.ArgumentParser(description='Draw a 3D-model from *.ply file')
    parser.add_argument('-model', help='Path to ply model file', default='icosahedron.ply')
    parser.add_argument('-f', '--faces', action='store_true', help='Draw faces', default=False)
    parser.add_argument('-e', '--edges', action='store_true', help='Draw edges', default=False)
    parser.add_argument('-s', '--silhouette', action='store_true', help='Draw silhouette', default=False)
    parser.add_argument('-l', '--lighting', action='store_true', help='Enable simple lighting', default=False)
    args = parser.parse_args()

    mesh = handlers[os.path.splitext(args.model)[1][1:]](args.model)
    mesh.scale()

    # Basic initialization - the same for most apps
    glutInit([])
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
    glutInitWindowSize(640, 480)
    glutCreateWindow("Simple OpenGL Renderer")
    glEnable(GL_CULL_FACE)
    glEnable(GL_DEPTH_TEST)           # Ensure farthest polygons render first
    glEnable(GL_NORMALIZE)            # Prevents scale from affecting color
    glClearColor(0.1, 0.1, 0.5, 0.0)  # Color to apply for glClear()

    # Callback functions for loop
    glutDisplayFunc(doRedraw)        # Runs when the screen must be redrawn
    glutIdleFunc(doIdle)             # Runs in a loop when the screen is not redrawn
    glutReshapeFunc(doReshape)       # Runs when the window is resized
    glutSpecialFunc(doSpecial)       # Runs when directional key is pressed
    glutKeyboardFunc(doKeyboard)     # Runs when key is pressed

    # Set up two lights
    BRIGHT4f = (1.0, 1.0, 1.0, 1.0)  # Color for Bright light
    DIM4f = (.2, .2, .2, 1.0)  # Color for Dim light
    if args.lighting:
        # glLightfv(GL_LIGHT0, GL_AMBIENT, BRIGHT4f)
        # glLightfv(GL_LIGHT0, GL_DIFFUSE, BRIGHT4f)
        glLightfv(GL_LIGHT0, GL_POSITION, brightLightPosition4f)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHTING)

    # Runs the GUI - never exits
    # Repeatedly calls doRedraw(), doIdle(), & doReshape()
    glutMainLoop()

