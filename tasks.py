from invoke import task
import os
import shutil

@task
def start(c):
    buildUI(c)
    c.run("python blaudio.py")

@task
def preview(c):
    buildUI(c)
    c.run("python ui/uipreview.py")

@task
def buildUI(c):
    c.run("pyuic6 ui/main_window.ui -o ui/main_window.py")
    c.run("pyuic6 ui/dynamic_slider.ui -o ui/dynamic_slider.py")
    
@task
def buildEXE(c):
    # Force full rebuild
    if os.path.exists("dist/"):
        shutil.rmtree("dist/")
    
    os.makedirs("dist/Arduino")
    c.run("pyinstaller blaudio.spec --clean")
    c.run("cp blaudio_config.json dist/")
    c.run ("cp Arduino/Nano/BlaudioNano/* dist/Arduino/")
    