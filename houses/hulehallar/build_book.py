"""Hulehällar 418D (Hamra, Gotland) – this house's own build step.

The Gotland 3D model is hand-written in scene.html (a standalone viewer you can open by itself). build_steps.py lifts the
scene out of that page, drops it into the house-book shell (engine/shell.html) and patches the shell for a plot with
several buildings (main house, guest house & garage, attefall house, the plot). Content is content.json.
Called by tools/build.py:  build(shell, house_dir) -> html."""
import os


def build(shell, hdir):
    ns = {'shell': shell, 'hdir': hdir}
    path = os.path.join(hdir, 'build_steps.py')
    exec(compile(open(path, encoding='utf-8').read(), path, 'exec'), ns)
    return ns['s']
