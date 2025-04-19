from PyQt6.QtGui import QOpenGLContext

print("OpenGL:", QOpenGLContext().format().profile())
