from invoke import task
import os
import shutil

@task
def start(c):
    c.run("python blaudio.py")

@task
def buildEXE(c):
    # Force full rebuild
    if os.path.exists("dist/"):
        shutil.rmtree("dist/")

    os.makedirs("dist/Arduino")
    c.run("pyinstaller blaudio.spec --clean")
    c.run("cp blaudio_config.json dist/")
    c.run("cp Arduino/Nano/BlaudioNano/* dist/Arduino/")
