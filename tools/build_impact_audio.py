"""Original contact sweeteners, layered under sampled effects; no external assets."""
import math
import random
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RATE = 44100


def build():
    output = ROOT/'assets/audio/impact'
    output.mkdir(parents=True, exist_ok=True)
    for name, duration in [('slash', .28), ('electric', .65), ('thunder', 1.15),
                           ('water', .72), ('fire', .95), ('illusion', .85), ('counter', .35)]:
        rng = random.Random('shinobi-impact-'+name)
        samples = []
        low = phase = 0.
        for n in range(round(duration*RATE)):
            t = n/RATE
            q = t/duration
            noise = rng.uniform(-1,1)
            low = low*.94 + noise*.06
            frequency = 48+95*math.exp(-t*30)
            phase += math.tau*frequency/RATE
            thump = math.sin(phase)*math.exp(-t*9)
            if name == 'illusion':
                value = .3*math.sin(math.tau*93*t)*math.exp(-t*5) + low*.8
                value += .18*math.sin(math.tau*187*t)*math.exp(-t*7)
            elif name == 'water':
                value = thump*.45+low*1.2+noise*.1*math.exp(-t*6)
            elif name == 'fire':
                value = thump*.65+low*1.8+noise*.1*math.exp(-t*8)
            elif name == 'counter':
                value = thump*.3+.2*math.sin(math.tau*640*t)*math.exp(-t*17)+noise*.15*math.exp(-t*30)
            else:
                value = thump*.7+low*(2 if name == 'thunder' else .7)
                value += noise*.22*math.exp(-t*(14 if name == 'electric' else 35))
            envelope = min(1,t/.004) * (1-q)**1.6
            samples.append(value*envelope)
        peak = max(abs(x) for x in samples)
        pcm = [round(x/peak*.65*32767) for x in samples]
        pcm[0] = pcm[-1] = 0
        with wave.open(str(output/f'{name}.wav'), 'wb') as stream:
            stream.setparams((1,2,RATE,0,'NONE','not compressed'))
            stream.writeframes(struct.pack('<'+'h'*len(pcm),*pcm))
    print('Built 7 original impact layers (44.1 kHz PCM, peak -3.7 dBFS)')


if __name__ == '__main__': build()
