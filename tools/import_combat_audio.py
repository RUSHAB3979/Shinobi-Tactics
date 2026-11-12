"""Rebuild sampled WAVs from retained masters and combat.json recipes (requires FFmpeg)."""
import array
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]


def decode(path, rate):
    result = subprocess.run([
        'ffmpeg', '-v', 'error', '-threads', '2', '-i', str(path),
        '-f', 's16le', '-ar', str(rate), '-ac', '1', 'pipe:1',
    ], capture_output=True, check=True)
    values = array.array('h', result.stdout)
    if sys.byteorder != 'little':
        values.byteswap()
    # Trim only outer silence, preserving quiet consonants with 35 ms padding.
    active = [i for i, value in enumerate(values) if abs(value) > 200]
    if not active:
        raise ValueError(f'Silent source: {path}')
    pad = round(rate*.035)
    return [v/32768 for v in values[max(0, active[0]-pad):active[-1]+pad+1]]


def build():
    manifest = json.loads((ROOT/'assets/audio/combat.json').read_text())
    rate = manifest['sample_rate']
    decoded = {}
    for key, source in manifest['source_files'].items():
        path = ROOT/source['path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != source['sha256']:
            raise ValueError(f'Source checksum changed: {path}')
        decoded[key] = decode(path, rate)
    output = ROOT/'assets/audio/sampled'
    output.mkdir(parents=True, exist_ok=True)
    metrics = {}
    for name, recipe in manifest['recipes'].items():
        mixed = []
        for layer in recipe['layers']:
            audio = decoded[layer['file']]
            start = round(layer['offset']*rate)
            end = start+round(layer['length']*rate) if layer['length'] else len(audio)
            audio = audio[start:end]
            if not audio:
                raise ValueError(f'Empty layer in {name}')
            if layer['reverse']:
                audio = audio[::-1]
            offset = round(layer['at']*rate)
            mixed.extend([0.] * max(0, offset+len(audio)-len(mixed)))
            for i, value in enumerate(audio):
                # Independent sample edges avoid clicks at each Sixfold slash.
                envelope = min(1, i/(rate*.006), (len(audio)-1-i)/(rate*.025))
                mixed[offset+i] += value * layer['gain'] * envelope
        peak = max(abs(v) for v in mixed)
        scale = recipe['peak']/max(peak, .00001)
        pcm = array.array('h', (round(v*scale*32767) for v in mixed))
        if sys.byteorder != 'little':
            pcm.byteswap()
        path = output/(name+'.wav')
        with wave.open(str(path), 'wb') as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(rate)
            stream.writeframes(pcm.tobytes())
        metrics[name] = dict(seconds=round(len(mixed)/rate, 4),
            peak=recipe['peak'], rms=round(math.sqrt(sum((v*scale)**2 for v in mixed)/len(mixed)), 4),
            sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    (ROOT/'docs/audio-metrics.json').write_text(json.dumps(metrics, indent=2)+'\n')
    print(f'Built {len(metrics)} sampled cues from {len(decoded)} checksummed masters')


if __name__ == '__main__':
    build()
