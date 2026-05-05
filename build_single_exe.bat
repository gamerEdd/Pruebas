@echo off
REM Build single-file executable for botgrafico.py using PyInstaller
REM Usage: run this in the project root where botgrafico.py is located.

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller







pause
necho Build finished. Output: dist\botgrafico.exe  --add-data "mi_sesion.session;." botgrafico.py  --hidden-import=MetaTrader5 --hidden-import=numpy --hidden-import=pandas --hidden-import=scipy --hidden-import=scikit_learn --hidden-import=sklearn ^pyinstaller --noconfirm --onefile --windowed --name botgrafico.exe ^nREM Build one-file windowed executable (no console). Remove --windowed to keep console.