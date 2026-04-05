# PyInstaller runtime hook for comtypes.
#
# In a frozen app, comtypes tries to write generated COM interface wrappers into
# a comtypes/gen/ directory inside _MEIPASS, which is read-only.  Setting
# gen_dir = None tells comtypes to generate everything in-memory instead,
# which prevents the IOError/PermissionError that would otherwise crash any
# thread that touches pycaw.
import comtypes.client
comtypes.client.gen_dir = None
