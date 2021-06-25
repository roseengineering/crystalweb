                                                                      
# Measure Crystal Characteristics Automatically Using a NanoVNA

![](animation.gif)

## Introduction

Use this script to automatically characterize your crystals
using a test fixture and a Nanovna.  The script will search for 
the series resonant point of the crystal and from there
make measurements.  It will also search for the parallel resonant point 
of the crystal, if the --stray option is given.
The parallel resonant frequency is used to find the crystal's "holder"
capacitance Co.

The script operates by drilling the Nanovna down to the series resonance point 
of the crystal and measuring its Cm, Lm, and Rm values using the phase shift 
method.  When the measurement is finished the Nanovna's 
sweep frequency range will be restored to what it was before the script was run.

## How to use

First set the start and stop "stimulus" values of the Nanovna to encompass the range
of frequencies you expect to see from your batch of crystals.  The 
frequency span should be large enough to capture
both the series and parallel resonant points of your crystals.  I
have been using a span of 100KHz.

Next calibrate the thru port of the Nanovna using the "calib" menu.
Now you can run the script to make the measurement.  Pass the --stray option 
if you want to measure the holder capacitance.  To
tell crystalweb explicitly what the start and stop frequency of the span you
want, pass the options --start and --stop to the program, otherwise it
will query the range from the nanovna.

The arguments to the python script are as follows:

                                                                 
```
$ crystalweb.py --help
usage: crystalweb.py [-h] [--fixture] [--loss] [--batch] [--theta THETA]
                     [--stray STRAY] [--repeat REPEAT] [--load LOAD]
                     [--part-name PART_NAME] [--part-number PART_NUMBER]
                     [--device DEVICE] [--start START] [--stop STOP]
                     [--capture]

optional arguments:
  -h, --help            show this help message and exit
  --fixture             measure test fixture stray capacitance (default:
                        False)
  --loss                measure test fixture loss (default: False)
  --batch               perform a batch measurement of crystals (default:
                        False)
  --theta THETA         phase angle for measuring bandwidth (default: 45)
  --stray STRAY         test fixture stray capacitance in pF, affects Co
                        (default: None)
  --repeat REPEAT       number of times to repeat measurements (default: 10)
  --load LOAD           test fixture source and load resistance (default: 50)
  --part-name PART_NAME
                        name of part (default: X)
  --part-number PART_NUMBER
                        number of part (default: 1)
  --device DEVICE       name of serial port device (default: None)
  --start START         starting frequency of initial sweep (default: None)
  --stop STOP           stopping frequency of initial sweep (default: None)
  --capture             capture screenshots of the measurements as
                        movie_xx.png (default: False)
```


## Measuring the Fixture Capacitance

Besides measuring crystals, the script can also measure the
stray capacitance of the test fixture using the "--fixture" measurement option.
When later measuring the crystal in the fixture, this stray capacitance is passed to crystalweb 
which it uses to find the crystal's holder capacitance.

Here are the steps to find the stray capacitance of your fixture. 
First calibrate the thru of the NanoVNA.  Next leave the fixture open 
and run "crystalweb.py --fixture".  The program will measure and output
the fixture's stray capacitance.

To find the dB loss through the fixture instead of the stray capacitance use the "--loss" option. 

## Example

The script, when it measures the crystal, writes the results it finds
immediately to stderr.  At the conclusion of the measurement, the script 
will then write a final comma separated 
formatted line, listing all the measurements previously found, to stdout.
The CSV header for this line is 'PART,FS,CM,LM,RM,QU,CO'.

For example, I executed the following to measure a 7.03 Mhz crystal:

```
$ crystalweb.py --stray 1.1
PART: X1
RL    = 50.0 ohm
fs    = 7027674 Hz
Rm    = 18.39 ohm
Cm    = 0.0149 pF
Lm    = 34.3163 mH
Qu    = 82401
fp    = 7039743 Hz
Co    = 3.25138 pF
X1,7027674,1.4946e-14,0.034316,18.39,82401,3.2514e-12
```

### My test fixture

![](fixture.jpg)

### Quantifying A Batch of 100 Crystals.

You can use the --batch option to quickly
measure a batch of crystals.  It will repeatedly run
the measurement after prompting you to change the crystal.

Below are the results from crystalweb, put in
graph form using Pandas, after measuring
100 crystals from a 11.0570 Mhz batch.

![](batch.png)

The top ten crystals, the ones with the highest unloaded Q,
have the following characteristics:

![](topten.png)


