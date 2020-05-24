                                                                      
# Measure Crystal Characteristic automatically using a NanoVNA

![](animation.gif)

Use this program to automatically characterize your crystals
using a text fixture and a Nanovna.  The script will search for 
the series frequency resonant point. (As well as the parallel resonant point 
if the stray option which is used to find the holder capacitance
of the crystal.)  
Namely the script will drill down to the series resonance point and 
measure the crystal's Cm, Lm, and Rm using the phase shift measurement 
method.

To use first set the "stimulus"
stop and start values of the Nanovna to encompass the range
of frequency your expect from your batch of crystals.  The 
frequency span should be large enough to capture
both the series and parallal resonant points of your crystals.

Next calibrate your Nanovna thru port using the Nanovna's "calib" menu.

The arguments to the python script follow:

                                                                 
```
$ crystalweb.py --help
usage: crystalweb.py [-h] [--fixture] [--loss] [--theta THETA] [--stray STRAY]
                     [--repeat REPEAT] [--load LOAD] [--title TITLE]
                     [--device DEVICE] [--start START] [--stop STOP]
                     [--capture]

optional arguments:
  -h, --help       show this help message and exit
  --fixture        measure test fixture stray capacitance (default: False)
  --loss           measure test fixture loss (default: False)
  --theta THETA    phase angle for measuring bandwidth (default: 45)
  --stray STRAY    test fixture stray capacitance in pF, affects Co (default:
                   None)
  --repeat REPEAT  number of times to repeat measurements (default: 10)
  --load LOAD      test fixture source and load resistance (default: 50)
  --title TITLE    title of measurement (default: )
  --device DEVICE  name of serial port device (default: None)
  --start START    starting frequency of initial sweep (default: None)
  --stop STOP      stopping frequency of initial sweep (default: None)
  --capture        capture screenshots of the measurements as movie_xx.png
                   (default: False)
```


Besides measuring crystals, the script can also measure the
stray capacitance of a test fixture using the "--fixture" option.

As the script measures a crystal it writes to stderr the result.  At the
conclusion of the measurement it then writes to stdout a comma separated 
formatted line of all the values found.  The csv header is for this
line is 'XTAL,FS,CM,LM,RM,QU,CO'.

For example here I used the script to measure a 7.03 Mhz crystal:

```
$ crystalweb.py --stray 1.1 --title X1
TITLE: X1
RL    = 50.0 ohm
fs    = 7027674 Hz
Rm    = 18.39 ohm
Cm    = 0.0149 pF
Lm    = 34.3163 mH
Qu    = 82401
stray = 1.10 pF
fp    = 7039743 Hz
Co    = 3.25138 pF
X1,7027674,1.4946e-14,0.034316,18.39,82401,3.2514e-12
```


