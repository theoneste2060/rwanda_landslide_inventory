@echo off

:: Define the array of district names
set "districts=Burera gakenke gicumbi musanze rulindo karongi nyabihu rubavu rusizi ngororero nyamasheke rutsiro nyamagabe"

:: Loop through each district and terminate the corresponding Python process
for %%d in (%districts%) do (
    taskkill /FI "WINDOWTITLE eq %%d - python predict.py"
)

pause
