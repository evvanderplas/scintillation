# scintillation

Software meant to read output of the Septentrio scintillation measurement instrument
and analyze its data to monitor space weather. GNSS satellites transmit radio waves
and the amplitude fluctuations and phase shift that are measured on the ground are a
measure for the change of the refractive index of the medium.

## Code
The code is in python, and uses numpy, pandas and matplotlib to analyze the data.

## SQLite

The scintillation data from SABA and SEUTA is read from csv files that come from the septentrio L0 interpreter.
This data is stored in a SQLite database. It contains parameters such as
Total Electron Content (TEC) and sigma phi (phase differences with different time intervals).
This data can be plotted as a function of track position (using azimuth and elevation) and time. 
