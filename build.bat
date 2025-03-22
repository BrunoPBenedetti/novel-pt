@echo off
echo Instalando dependencias...
pip install -r requirements.txt
pip install pyinstaller

echo Limpando builds anteriores...
rmdir /s /q build
rmdir /s /q dist

echo Gerando executavel...
pyinstaller --clean novel_pt.spec

echo Build concluido!
echo O executavel esta na pasta dist
pause
