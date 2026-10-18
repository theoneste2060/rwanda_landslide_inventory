@echo off

:: Define the array of district names
set "districts=Burera gakenke gicumbi musanze rulindo karongi nyabihu rubavu rusizi ngororero nyamasheke rutsiro nyamagabe"

:: Loop through each district and open a new terminal window to run the Python script
for %%d in (%districts%) do (
    start cmd /k python "%%d\predict.py"
)

pause
