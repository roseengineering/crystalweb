#!/usr/bin/python3
import argparse, serial, time, sys
import numpy as np
from serial.tools import list_ports


def capture():
    global capture_num
    from PIL import Image
    import struct
    send_command("capture")
    b = _dev.read(320 * 240 * 2)
    x = struct.unpack(">76800H", b)
    arr = np.array(x, dtype=np.uint32)
    arr = 0xFF000000 + ((arr & 0xF800) >> 8) + ((arr & 0x07E0) << 5) + ((arr & 0x001F) << 19)
    img = Image.frombuffer('RGBA', (320, 240), arr, 'raw', 'RGBA', 0, 1)
    img.save("movie_%02d.png" % capture_num)
    capture_num += 1

### NANOVNA FUNCTIONS

def getport():
    VID = 0x0483
    PID = 0x5740
    device_list = list_ports.comports()
    for device in device_list:
        if device.vid == VID and device.pid == PID:
            return device.device
    raise OSError("device not found")

def send_command(cmd):
    cmd += "\r"
    _dev.write(cmd.encode())
    _dev.readline()

def marker_command(number, index):
    send_command("marker {:d} {:s}".format(number, str(index)))

def fetch_data():
    result = []
    line = ''
    while True:
        c = _dev.read().decode()
        if c == chr(13):
            pass 
        elif c == chr(10):
            result.append(line.split(' '))
            line = ''
        else:
            line += c
            if line.endswith('ch>'):
                break
    return result

def sweep(start=None, stop=None):
    if start and stop:
        if stop - start < 100: 
            fs = (start + stop) /2
            start, stop = fs - 50, fs + 50
        send_command("sweep {:d} {:d}".format(int(start), int(stop)))
    send_command("sweep")
    start, stop, _ = [ int(x) for x in fetch_data()[0] ]
    if stop < 0:
        start = start + stop / 2
        stop = start - stop
    return start, stop

def thru():
    send_command("data 1")
    data = fetch_data()
    return np.array([ np.complex(float(re), float(im)) for re,im in data ])

def frequencies():
    send_command("frequencies")
    return np.array([ int(x[0]) for x in fetch_data() ])

def open_port(filename, start=None, stop=None):
    global _dev, _start, _stop
    _dev = serial.Serial(filename)
    _start, _stop = sweep(start=start, stop=stop)

def close_port():
    sweep(start=_start, stop=_stop)
    _dev.close()


#### CRYSTAL CHARACTERIZATION FUNCTIONS

def motational_resistance(loss, rl):
    RM = 2 * rl * (10**(loss/20) - 1)
    return RM

def phase_shift_method(fs, bw, rm, rl, theta):
    REFF = rm + 2 * rl
    CM = bw / (2 * np.pi * REFF * fs**2 * np.tan(theta * np.pi / 180))
    LM = 1 / (2 * np.pi * fs)**2 / CM
    QU = 2 * np.pi * fs * LM / rm
    return CM, LM, QU

def holder_parallel(fs, fp, cm, stray):
    co = cm / (fp / fs - 1) / 2 - stray
    return co

def stray_fixture(freq, loss, rl):
    xc = 2 * rl * (10**(loss/20) - 1)
    stray = 1 / (2 * np.pi * freq * xc)
    return stray


#### MAIN CODE

def measure(N, theta=45, tol=2):
    time.sleep(1)
    freq = frequencies()
    i = 0
    data = []
    last = None
    while i < N:
        d = thru()
        if np.all(last == d): continue
        data.append(d)
        last = d
        i += 1
    data = np.array(data)
    mag = np.median(20 * np.log10(np.abs(data)), axis=0)
    phi = np.median(np.angle(data) * 180 / np.pi, axis=0)
    i = np.where(np.diff(np.sign(phi)) != 0)[0]
    zeros = freq[i]
    gain = mag[i]
    fmin = freq[np.argmin(mag)]
    fmax =  freq[np.argmax(mag)]

    bw = np.nan
    if phi[0] > theta + tol and phi[-1] < -(theta + tol):
        span = np.interp([theta, -theta], phi[::-1], freq[::-1])
        bw = span[1] - span[0]

    if "capture_num" in globals(): capture()
    return (zeros, gain, bw), (fmin, fmax), (freq, mag)

def analyze_loss(N, rl):
    _, mag = measure(N=N)[2]
    print('Test fixture loss')
    print('maximum = {:.2f} dB'.format(np.max(mag)), file=sys.stderr)
    print('median  = {:.2f} dB'.format(np.median(mag)), file=sys.stderr)
    print('minimum = {:.2f} dB'.format(np.min(mag)), file=sys.stderr)

def analyze_stray(N, rl):
    freq, mag = measure(N=N)[2]
    stray = stray_fixture(freq=freq, loss=-mag, rl=rl)
    print('Test fixture capacitance')
    print('maximum = {:.2f} pF'.format(np.max(stray) / 1e-12), file=sys.stderr)
    print('median  = {:.2f} pF'.format(np.median(stray) / 1e-12), file=sys.stderr)
    print('minimum = {:.2f} pF'.format(np.min(stray) / 1e-12), file=sys.stderr)

def analyze_crystal(N, rl, theta, stray, title):
    NFSFP = 1
    NFS = 1
    NFP = 1
    alpha = .7

    # get initial measurement

    marker_command(1, "on")
    marker_command(1, 0)
    if title: print("TITLE: {}".format(title), file=sys.stderr)
    print("RL    = {:.1f} ohm".format(rl), file=sys.stderr)
    fp, fs = measure(N=NFSFP)[1]

    # measure fs

    df = fp - fs
    bw_df = None
    while df > 100:
        df = alpha * df
        sweep(fs - df/2, fs + df/2)
        marker_command(1, 50)
        zeros, gain, bw = measure(N=NFS if df > 100 else N, theta=theta)[0]
        if not np.isnan(bw): bw_df = df 
        fs = zeros[0]
        loss = -gain[0]
    print("fs    = {:.0f} Hz".format(fs), file=sys.stderr)
    rm = motational_resistance(loss, rl)
    print("Rm    = {:.2f} ohm".format(rm), file=sys.stderr)

    # measure bandwidth
    
    sweep(fs - bw_df / 2, fs + bw_df / 2)
    _, _, bw = measure(N=N, theta=theta)[0]
    cm, lm, qu = phase_shift_method(fs=fs, bw=bw, rm=rm, rl=rl, theta=theta)
    print("Cm    = {:.4f} pF".format(cm / 1e-12), file=sys.stderr)
    print("Lm    = {:.4f} mH".format(lm / 1e-3), file=sys.stderr)
    print("Qu    = {:.0f}".format(qu), file=sys.stderr)

    # drill down fp

    if stray is None:
        co = 0
    else:
        stray = stray * 1e-12
        print('stray = {:.2f} pF'.format(stray / 1e-12), file=sys.stderr)
        df = fp - fs
        while df > 100:
            df = alpha * df
            sweep(fp - df / 2, fp + df / 2)
            marker_command(1, 50)
            fp, _ = measure(N=NFP if df > 100 else N)[1]
        print("fp    = {:.0f} Hz".format(fp), file=sys.stderr)
        co = holder_parallel(fs=fs, fp=fp, cm=cm, stray=stray)
        print('Co    = {:.5f} pF'.format(co / 1e-12), file=sys.stderr)

    print("{title},{fs:.0f},{cm:.5g},{lm:.5g},{rm:.2f},{qu:.0f},{co:.5g}".format(
          title=title, fs=fs, cm=cm, lm=lm, rm=rm, co=co, qu=qu))
    sys.stdout.flush()

def main():
    global capture_num
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--fixture", action="store_true",
        help="measure test fixture stray capacitance")
    parser.add_argument("--loss", action="store_true",
        help="measure test fixture loss")
    parser.add_argument("--theta", type=float, default=45,
        help="phase angle for measuring bandwidth")
    parser.add_argument("--stray", type=float,
        help="test fixture stray capacitance in pF, affects Co")
    parser.add_argument("--repeat", type=int, default=10,
        help="number of times to repeat measurements")
    parser.add_argument("--load", type=int, default=50,
        help="test fixture source and load resistance")
    parser.add_argument("--title", type=str, default='',
        help="title of measurement")
    parser.add_argument("--device", 
        help="name of serial port device")
    parser.add_argument("--start", type=float, 
        help="starting frequency of initial sweep")
    parser.add_argument("--stop", type=float, 
        help="stopping frequency of initial sweep")
    parser.add_argument("--capture", action="store_true",
        help="capture screenshots of the measurements as movie_xx.png")

    args = parser.parse_args()
    if args.capture: capture_num = 0
    N = args.repeat
    rl = args.load
    theta = args.theta
    open_port(args.device or getport(), start=args.start, stop=args.stop)
    err = 0
    try:
        if args.fixture:
            analyze_stray(N=N, rl=rl)
        elif args.loss:
            analyze_loss(N=N, rl=rl)
        else:
            analyze_crystal(N=N, rl=rl, theta=theta, 
                stray=args.stray, title=args.title)
    except KeyboardInterrupt:
        print("Bye", file=sys.stderr)
        err = 1
    except Exception:
        import traceback
        traceback.print_exc()
        err = 1
    close_port()
    sys.exit(err)


if __name__ == "__main__":
    main()

