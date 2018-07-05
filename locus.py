#!/usr/bin/python3
"""Culla generates a desktop theme using colours
from the current wallpaper"""

import sys
import random
import os.path
import subprocess
import time
import colorsys
from collections import namedtuple
from math import sqrt
import dbus

if sys.version_info[1] < 4:
    print("Culla requires Python 3.4 or later.")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Python3 Pillow is required.")
    sys.exit(1)

#Colours for our Plasma theme
plasma_colors = """[Colors:Window]
ForegroundNormal=bbb
BackgroundNormal=aaa

[Colors:Selection]
BackgroundNormal=eee

[Colors:Button]
ForegroundNormal=248,248,248
BackgroundNormal=fff
DecorationFocus=ggg

[Colors:Compilmentary]
BackgroundNormal=4,4,222

[Colors:View]
BackgroundNormal=ccc
ForegroundNormal=242,242,242
DecorationHover=ddd"""


# http://charlesleifer.com/blog/using-python-and-k-means-to-find-the-dominant-colors-in-images/
Point = namedtuple('Point', ('coords', 'n', 'ct'))
Cluster = namedtuple('Cluster', ('points', 'center', 'n'))

def get_points(img):
    points = []
    w, h = img.size
    for count, color in img.getcolors(w * h):
        points.append(Point(color, 3, count))
    #return points
    return [Point(color, 3, count) for count, color in img.getcolors(w * h)]

rtoh = lambda rgb: '#%s' % ''.join(('%02x' % p for p in rgb))

def colorz(filename, n=3):
    img = Image.open(filename)
    img.thumbnail((96, 96))
    w, h = img.size

    points = get_points(img)
    clusters = kmeans(points, n, 1)
    rgbs = [map(int, c.center.coords) for c in clusters]
    return map(rtoh, rgbs)

def euclidean(p1, p2):
    return sqrt(sum([
        (p1.coords[i] - p2.coords[i]) ** 2 for i in range(p1.n)
    ]))

def calculate_center(points, n):
    vals = [0.0 for i in range(n)]
    plen = 0
    for p in points:
        plen += p.ct
        for i in range(n):
            vals[i] += (p.coords[i] * p.ct)
    if plen == 0:   #Fix divide-by-zero bug in original code
        plen = 1
    return Point([(v / plen) for v in vals], n, 1)

def kmeans(points, k, min_diff):
    clusters = [Cluster([p], p, p.n) for p in random.sample(points, k)]

    while True:
        plists = [[] for i in range(k)]

        for p in points:
            smallest_distance = float('Inf')
            for i in range(k):
                distance = euclidean(p, clusters[i].center)
                if distance < smallest_distance:
                    smallest_distance = distance
                    idx = i
            plists[idx].append(p)

        diff = 0
        for i in range(k):
            old = clusters[i]
            center = calculate_center(plists[i], old.n)
            new = Cluster(plists[i], center, old.n)
            clusters[i] = new
            diff = max(diff, euclidean(old.center, new.center))

        if diff < min_diff:
            break

    return clusters


#------ locus Functions ------------------------------------------------
def color_triplet(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h, s, v)

    if r > 1.0:
        r = 1.0
    r = int(r * 255)

    if g > 1.0:
        g = 1.0
    g = int(g * 255)

    if b > 1.0:
        r = 1.0
    b = int(b * 255)

    return ','.join([str(r), str(g), str(b)])


def aurorae(rgb):
    """Open decoration template, substitue our colour
    then write decoration.svg"""

    try:
        with open(os.path.expanduser \
            ('~/.local/share/aurorae/themes/locus/decoration-template.svg')) \
            as f:
            auroraetemplate = f.read()
    except IOError:
        fatal("Unable to find locus template.")

    r, g, b = rgb.split(',')
    hex_colour = f'#{int(r):02x}{int(g):02x}{int(b):02x}'
    auroraetemplate = auroraetemplate.replace('TEMPLAT', hex_colour)

    try:
        with open(os.path.expanduser \
            ('~/.local/share/aurorae/themes/locus/decoration.svg'), 'w') as f:
            f.write(auroraetemplate)
    except IOError:
        fatal("Fatal. Unable to write aurorae decoration.")


    session_bus = dbus.SessionBus()

    if [k for k in session_bus.list_names() if 'KWin' in k]:
        proxy = session_bus.get_object('org.kde.KWin', '/KWin')
        subprocess.run(['kbuildsycoca5'], stderr=subprocess.DEVNULL)
        subprocess.run(['kwriteconfig5', '--file=kwinrc',
                        '--group=org.kde.kdecoration2',
                        '--key=theme', '__aurorae__svg__locus'])
        proxy.reconfigure()
    else:
        fatal('Unable to find KWin. Is it running?')

def fatal(message):
    """Something's wrong."""
    print(message)
    sys.exit(1)

#---------------- locus ------------------------------------------------
#Raise flag when finding correct session in plasmarc
flag = False
#Holder for current activity ID
activity = ""

try:
    with open(os.path.expanduser( \
        '~/.config/plasma-org.kde.plasma.desktop-appletsrc')) as f:
        plasmaconfig = f.readlines()
except:
    fatal('Fatal. Unable to find plasma config.')


try:
    with open(os.path.expanduser('~/.config/kactivitymanagerdrc')) as f:
        activityrc = f.readlines()
except:
    print('Unable to find kactivity manager rc.')
    activityrc = None
    flag = True   #There is only default activity

#Retrieve current activity
if activityrc is not None:
    a = [a for a in activityrc if 'current' in a]
    a = a[0].split('=')
    activity = a[1].rstrip()

#Flag if wallpaper is found
found = False

#Find current activity then grab next Image= key
for line in plasmaconfig:
    if activity in line:
        flag = True
    if 'Image=' in line and flag:
        found = True
        break

if not found:
    print("I didn't find your wallpaper. Have you set one yet?")
    sys.exit(1)

tmp, wallpaper = line.split('//')
wallpaper = wallpaper.strip()

if not os.path.isfile(wallpaper):
    print("I think the wallpaper is {0} but I can't find it. Exiting."
          .format(wallpaper))
    sys.exit(1)

#Get samples from the image
colorslist = list(colorz(wallpaper.rstrip(), 3))

#Choose darkest returned colour
image_value = 1.0
h_base = 0.0
s_base = 0.0
v_base = 0.0

for x in colorslist:
    r, g, b = tuple(int(x[i:i+2], 16) for i in (1, 3, 5))
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)

    if v <= image_value:   #Choose darkest
        h_base = h
        s_base = s
        v_base = v
        image_value = v


print("BASE HSV  ", h_base, s_base, v_base)

s_panel = s_base

if s_base < 0.93:
    s_panel += 0.06

#Panel Background
panel_background = (color_triplet(h_base, s_panel, v_base))

#Window Decoration saturation 
s_window = 0.75

if s_base < 0.04:
    s_window = 0.0

#Color Scheme Window Decoration and Selection
window_decoration_color = color_triplet(h_base, s_window, 0.75)

#Default text colour
foreground = "242,242,242"

#Minimised taskbar
minimised_task = "36,36,36"
s_button = s_base

#Hues relative to base
v_dialog = v_base + 0.09
s_dialog = s_base - 0.09

#Alternate shade for dialog backgrounds
dialog_background = color_triplet(h_base, s_dialog, v_dialog)

if s_base < 0.88 and s_base > 0.08:
    s_frame = s_base + 0.12
    s_button = s_base + 0.12
    s_selection = s_base + 0.12

v_frame = 0.45
v_button = 0.4
v_selection = 0.4
#s_selection = 0.45

s_frame = 0.5

if s_base < 0.04:
    s_frame = 0.0

#Frame and button hover
frame = color_triplet(h_base, s_frame, 0.9)

#Plasma selection and button background
highlight_color = color_triplet(h_base, s_button, v_button)



#Color Scheme Focus
focus_offset = 0.06

#Focus
#focus_decoration_color = color_triplet(h_base, l_selection + focus_offset,
                                       #s_selection - focus_offset)

s_focus = s_base

if s_focus > 0.04:
    s_focus /= 4

focus_decoration_color = color_triplet(h_base, s_focus, 0.98)

plasma_colors = plasma_colors.replace('aaa', panel_background)
plasma_colors = plasma_colors.replace('bbb', foreground)
plasma_colors = plasma_colors.replace('ccc', dialog_background)
plasma_colors = plasma_colors.replace('ddd', frame)
plasma_colors = plasma_colors.replace('eee', highlight_color)
plasma_colors = plasma_colors.replace('fff', highlight_color)
plasma_colors = plasma_colors.replace('ggg', minimised_task)

try:
    with open(os.path.expanduser( \
        '~/.local/share/plasma/desktoptheme/locus/colors'), 'w') as f:
        f.write(plasma_colors)
except:
    fatal("Unable to open locus Plasma colors. Is it installed?")

try:
    subprocess.run(['kwriteconfig5', '--file=plasmarc',
                    '--group=Theme', '--key=name', 'Default'])

    #Do this too quickly and Plasma won't change
    time.sleep(0.5)

    subprocess.run(['kwriteconfig5', '--file=plasmarc',
                    '--group=Theme', '--key=name', 'locus'])
except IOError as e:
    print(e)
    fatal("Fatal. Unable to run kwriteconfig.")

try:
    subprocess.run(['kwriteconfig5', '--file=kdeglobals',
                    '--group=Colors:Selection',
                    '--key=BackgroundNormal', focus_decoration_color])
    subprocess.run(['kwriteconfig5', '--file=kdeglobals',
                    '--group=Colors:View',
                    '--key=DecorationFocus',
                    focus_decoration_color])
    subprocess.run(['kwriteconfig5', '--file=kdeglobals',
                    '--group=WM',
                    '--key=activeBackground',
                    window_decoration_color])
except:
    fatal("Fatal. Unable to run kwriteconfig.")


#If Culla window dec is active, update it
aur_theme = subprocess.run(['kreadconfig5', '--file=kwinrc',
                            '--group=org.kde.kdecoration2', '--key=theme'], \
                            stdout=subprocess.PIPE)

if b'locus' in aur_theme.stdout:
    aurorae(window_decoration_color)
