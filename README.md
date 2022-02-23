# Sage_GUI
GUI for sage

## Data Definition
__*Target Status*__: Status indicating the measurement validity. It is type `uint8_t` and is one of the member variable of type `VL53L5CX_ResultsData`  
__*Distance__mm*__: Measured distance in mm. It is type `int16_t` and is one of the member variable of type `VL53L5CX_ResultsData`  
__*Reflectance*__: Estimated reflectance in percent. It is type `uint8_t` and is one of the member variable of type `VL53L5CX_ResultsData`

## Using guide for reflectance test example 
- Download the code `Example_1_ranging_basic.c` (it is a modified version) into the folder `../VL53L5CX_Linux_driver_1.1.2/user/examples` and replace the old one.
- Go to `../VL53L5CX_Linux_driver_1.1.2/user/test` and use make command to compile.
- Run `menu` and choose example 1.
