"""
========================================================================
███    ██ ███████ ██████   ██████   ██████  ███████ ██████  ██ ████████
████   ██ ██           ██ ██       ██  ████ ██      ██   ██ ██    ██
██ ██  ██ ███████  █████  ███████  ██ ██ ██ █████   ██   ██ ██    ██
██  ██ ██      ██      ██ ██    ██ ████  ██ ██      ██   ██ ██    ██
██   ████ ███████ ██████   ██████   ██████  ███████ ██████  ██    ██
========================================================================

NS360Edit: a save editor for NFS Most Wanted (2005), Xbox 360.

Edits vehicle bounty and player cash in MC02 saves from the Apple
Silicon native recomp build. Reads the save, applies the edits,
recomputes the MD5 and CRC32 checksums and writes a new file.

Files:
    main.py         entry point
    gui.py          PyQt6 window
    filehandler.py  save parsing, editing and checksums
    carnames.py     LUT for vehicle signatures 

Usage:
    python3 main.py

Credits:
    The EA CRC32 algorithm, vehicle record layout, vehicle signature-name LUT
    come from the NFS MW Save Editor by sprintstate and BaZZtian (PC).

Author: anode-anode [2026]
"""
#main.py
import sys
from PyQt6.QtWidgets import QApplication
import gui
import qdarktheme

def main():
    app = QApplication(sys.argv)

    window = gui.SaveGui()
    app.setStyleSheet(qdarktheme.load_stylesheet())
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
