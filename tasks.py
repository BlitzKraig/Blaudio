from invoke import task

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
    
    