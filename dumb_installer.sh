#!/bin/sh


NONE='\e[0m'
RED='\e[1;31m'
YELLOW='\e[1;33m'
GREEN='\e[1;32m'
BLUE='\e[1;34m'

AURORAE="${HOME}/.local/share/aurorae/themes"
PLASMA="${HOME}/.local/share/plasma/desktoptheme"
BIN="${HOME}/.local/bin"
SCHEME="${HOME}/.local/share/color-schemes"
APPS="${HOME}/.local/share/applications"
PIXMAP="${HOME}/.local/share/pixmaps"
QTCURVE="$HOME/.local/share/QtCurve"


python3 -c "from PIL import Image" 2>/dev/null
PIL=$?

if [ "$PIL" -gt 0 ]; then
    echo -e "${RED}locus requires Python3 Pillow. This should be available"
    echo "from your package manager otherwise you could try"
    echo "'sudo pip3 install pillow'. In Ubuntu, this may"
    echo -e "be called python3-pil.${NONE}"
    exit 1
else
    echo -e "${GREEN}Python3 Pillow found. Continuing...${NONE}"
fi

if [ ! -d "$AURORAE" ]; then
    echo -e "${YELLOW}Creating Aurorae theme directory${NONE}"
    mkdir -pv "$AURORAE"
fi

echo -e "${GREEN}Copying Aurorae theme${NONE}"
cp -rf themes/locus  "$AURORAE"


if [ ! -d "$PLASMA" ]; then
    echo -e "${YELLOW}Creating Plasma theme directory${NONE}"
    mkdir -pv "$PLASMA"
fi

echo -e "${GREEN}Copying Plasma theme${NONE}"
cp -rf desktoptheme/locus "$PLASMA"


if [ ! "$BIN" ];then
    echo -e "${YELLOW}Creating local bin directory${NONE}"
    mkdir -pv "$BIN"
fi

echo -e "${GREEN}Copying locus script${NONE}"
cp -vf locus.py "$BIN"

if [ ! -x "$BIN"/locus.py ]; then
    echo -e "${YELLOW}Setting script executable${NONE}"
    chmod -v 755 "$BIN"/locus.py
fi


if [ ! -d "$SCHEME" ]; then
    echo -e "${YELLOW}Creating color-schemes directory${NONE}"
    mkdir -pv "$SCHEME"
fi

echo -e "${GREEN}Copying color-scheme${NONE}"
cp -vf Locus.colors "$SCHEME"


if [ ! -d "$APPS" ]; then
    echo -e ${YELLOW}"Creating local applications directory${NONE}"
    mkdir -pv "$APPS"
fi

echo -e "${GREEN}Copying menu desktop entry${NONE}"
cp -v locus.desktop "$APPS"


if [ ! -d "$PIXMAP" ]; then
    echo -e "${YELLOW}Creating local pixmap directory${NONE}"
    mkdir -pv "$PIXMAP"
fi

echo -e "${GREEN}Copying pixmap${NONE}"
cp -v locus.png "$PIXMAP"


if [ ! -d "$QTCURVE" ]; then
    echo -e "${YELLOW}Creating local QtCurve directory${NONE}"
    mkdir -pv "$QTCURVE"
fi

echo -e "${GREEN}Copying QtCurve theme${NONE}"
cp -v locus.qtcurve "$QTCURVE"

echo
echo -e "${BLUE}Setting window decoration to locus"
kwriteconfig5 --file=kwinrc --group=org.kde.kdecoration2 --key=library org.kde.kwin.aurorae
kwriteconfig5 --file=kwinrc --group=org.kde.kdecoration2 --key=theme "__aurorae__svg__locus"
qdbus  org.kde.KWin /KWin org.kde.KWin.reconfigure

echo -e "${BLUE}Setting desktop to locus"
"$HOME"/.local/bin/locus.py

echo -e "${YELLOW}Set locus colors from SystemSettings. Set QtCurve application"
echo -e "style and select the locus preset.${NONE}"
echo
echo -e "${YELLOW}You may need to add ~/.local/bin to your PATH${NONE}"
echo
