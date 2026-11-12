"""Reproducible original game cues, using only the Python standard library."""
import math
import random
import struct
import wave
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RATE=22050
CHARACTERS={"sasuke":250,"tanjiro":330,"itachi":185,"zenitsu":440}


def build():
    output=ROOT/"assets/audio/generated"
    output.mkdir(parents=True,exist_ok=True)
    for char,base in CHARACTERS.items():
        for action in ("attack","jutsu","ultimate","heal","hit","block"):
            duration={"attack":.20,"jutsu":.42,"ultimate":.68,"heal":.40,"hit":.12,"block":.18}[action]
            rng=random.Random(char+action)
            samples=[]
            phase=0
            for i in range(int(RATE*duration)):
                t=i/RATE
                progress=t/duration
                envelope=min(1,t/.008)*(1-progress)**1.8
                if action=="heal":
                    frequency=base*(1+int(progress*4)*.25)
                elif action in ("hit","block"):
                    frequency=base*(1.2-.9*progress)
                else:
                    frequency=base*(2.4-1.7*progress)
                phase+=math.tau*frequency/RATE
                tone=math.sin(phase)*.45+math.sin(phase*2)*.15
                noise=rng.uniform(-1,1)*(.55 if action in ("attack","hit") else .12)
                value=(tone+noise)*envelope*.35
                samples.append(round(max(-1,min(1,value))*32767))
            with wave.open(str(output/f"{char}-{action}.wav"),"wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(RATE)
                wav.writeframes(struct.pack("<"+"h"*len(samples),*samples))
    build_powers(output)
    print("Built 24 original cues, including 8 layered move-specific power cues")


def build_powers(output):
    """Release-to-impact sound design; seeded noise, no sampled recordings."""
    for char in CHARACTERS:
        for action in ('jutsu','ultimate'):
            impact=.32 if action=='jutsu' else (.50 if char in ('tanjiro','zenitsu') else .60)
            duration=impact+.30
            rng=random.Random('powers-v2-'+char+action)
            samples=[];low=0.;phase=0.
            for i in range(round(RATE*duration)):
                t=i/RATE;q=min(1,t/impact)
                noise=rng.uniform(-1,1);low=low*.88+noise*.12
                attack=min(1,t/.012);tail=math.exp(-max(0,t-impact)*15)
                contact=math.exp(-max(0,t-impact)*22) if t>=impact else 0
                if char=='sasuke' and action=='jutsu':
                    phase+=math.tau*(1100+q*1900)/RATE
                    crack=(noise-low)*(.2+.4*abs(math.sin(t*101)))
                    value=(math.sin(phase)*.12+crack)*attack*tail+low*contact*.8
                elif char=='sasuke':
                    value=(low*1.4+math.sin(t*math.tau*47)*.12)*(q*.6+contact)*tail
                    value+=(noise-low)*.17*contact
                elif char=='itachi' and action=='jutsu':
                    flutter=(.5+.5*math.sin(t*math.tau*19))**5
                    value=(low*.8+(noise-low)*.1)*flutter*tail
                    value+=math.sin(t*math.tau*340)*.08*(1-q)*attack
                elif char=='itachi':
                    value=(math.sin(t*math.tau*83)+math.sin(t*math.tau*87))*.10*attack*tail
                    value+=low*.5*contact+math.sin(t*math.tau*530)*.06*(1-q)
                elif char=='tanjiro' and action=='jutsu':
                    modulation=.4+.6*math.sin(t*math.tau*7)**2
                    value=(low*.9+(noise-low)*.12)*modulation*attack*tail+low*.5*contact
                elif char=='tanjiro':
                    value=(low*1.5+(noise-low)*.24)*attack*tail*(.3+.7*q)
                    value+=math.sin(t*math.tau*(70+q*40))*.1*contact
                elif action=='jutsu':
                    value=low*.2*tail
                    for k in range(6):
                        d=t-impact*k/6
                        if 0<=d<.085:value+=(noise*.25+math.sin(d*math.tau*(1500-d*9000))*.12)*math.exp(-d*35)
                    value+=low*.7*contact
                else:
                    phase+=math.tau*(2800-q*2100)/RATE
                    value=((noise-low)*.26+math.sin(phase)*.14)*attack*tail+low*.8*contact
                samples.append(value)
            peak=max(.01,max(abs(v) for v in samples))
            pcm=[round(v/peak*.66*32767) for v in samples]
            with wave.open(str(output/f'{char}-{action}.wav'),'wb') as wav:
                wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(RATE)
                wav.writeframes(struct.pack('<'+'h'*len(pcm),*pcm))


if __name__=="__main__":build()
