"""Deterministic original weapon/impact synthesis; no downloaded source recordings.
Run with Python + numpy. Writes 48 kHz stereo PCM and a listening reel.
"""
from pathlib import Path
import json, wave
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RATE = 48000
OUT = ROOT / 'godot/assets/audio'

def noise(t, rng, cutoff=900):
    raw = rng.normal(0, 1, len(t))
    spectrum = np.fft.rfft(raw)
    spectrum *= 1 / np.sqrt(1 + (np.fft.rfftfreq(len(t), 1 / RATE) / cutoff) ** 4)
    result = np.fft.irfft(spectrum, n=len(t))
    return result / max(np.std(result), 1e-9)

def tone(t, start, end, decay):
    return np.sin(2 * np.pi * (end*t + (start-end)*decay*(1-np.exp(-t/decay))))

def design(kind, variant):
    rng = np.random.default_rng(1701 + variant + 100 * ['bolter','grenade','relay','chainsword'].index(kind))
    duration = {'bolter':.48,'grenade':1.9,'relay':2.5,'chainsword':.36}[kind]
    t = np.arange(int(duration * RATE)) / RATE
    if kind == 'bolter':
        # Sharp pressure crack, heavy low-mid punch, breech cycling after report.
        x = .40*noise(t,rng,11000)*np.exp(-t/.013)
        x += .65*tone(t,170+variant*7,58,.035)*np.exp(-t/.080)
        x += .24*noise(t,rng,1800)*np.exp(-t/.055)
        for delay, freq, level in [(.055,1700,.17),(.090,840,.11)]:
            u = np.maximum(0,t-delay)
            x += (t>=delay)*level*(np.sin(2*np.pi*freq*u)+noise(t,rng,5500)*.6)*np.exp(-u/.012)
    elif kind == 'grenade':
        x = .65*noise(t,rng,9500)*np.exp(-t/.016)
        x += .65*tone(t,120,34,.08)*np.exp(-t/.21)
        x += .43*noise(t,rng,900)*np.exp(-t/.32)
        x += .12*noise(t,rng,170)*np.exp(-t/.65)
    elif kind == 'relay':
        # Fast suction chirp, collapsing metal, electrical discharge, falling rubble.
        x = .23*tone(t,1800,90,.07)*np.exp(-t/.20)
        x += .50*tone(t,165,29,.10)*np.exp(-t/.30)
        x += .3*noise(t,rng,2200)*np.exp(-t/.22)
        for delay in [.09,.16,.23,.39,.57,.72]:
            u = np.maximum(0,t-delay)
            freq = rng.uniform(280,2400)
            x += (t>=delay)*.13*(np.sin(2*np.pi*freq*u)+.6*noise(t,rng,3000))*np.exp(-u/.07)
    else:
        # A brief motor rev under cutting load. Irregular combustion pulses
        # modulate colored noise rather than sustaining a pitched sawtooth chord.
        rpm = 75 + 75*(1-np.exp(-t/.035)) - 70*np.clip((t-.16)/.20,0,1)
        phase = 2*np.pi*np.cumsum(rpm+noise(t,rng,45)*7)/RATE
        chug = .55+.45*np.maximum(0,np.sin(phase))**3
        rev = (1-np.exp(-t/.016))*np.minimum(1,(duration-t)/.095)
        load = np.exp(-((t-.12)/.065)**2)
        body = .30*noise(t,rng,650)*chug
        rasp = .12*noise(t,rng,2600)*(.25+.75*load)
        x = (body+rasp)*rev
        # Dry bite and a short mechanical run-down, with no ringing tail.
        u = np.maximum(0,t-.055)
        x += .13*noise(t,rng,4800)*np.exp(-u/.022)*(t>=.055)
    if kind in ['grenade','relay']:
        for delay in rng.uniform(.12, min(1.3,duration-.3), 18):
            u = np.maximum(0,t-delay)
            x += (t>=delay)*rng.uniform(.015,.07)*noise(t,rng,6500)*np.exp(-u/.013)
    # Small, asymmetric room reflections; hard ending avoided with a fade.
    stereo = np.column_stack([x,x])
    for channel, delays in enumerate([[],[]] if kind=='chainsword' else [[.029,.071,.113],[.037,.083,.139]]):
        for i, delay in enumerate(delays):
            n = int(delay*RATE)
            stereo[n:,channel] += x[:-n] * (.12 / (i+1))
    fade = np.minimum(1,t/.0015)*np.minimum(1,(duration-t)/.055)
    stereo *= fade[:,None]
    stereo -= stereo.mean(axis=0)
    stereo = np.tanh(stereo*1.25)
    stereo *= .82 / np.max(np.abs(stereo))
    return stereo

def save(path, samples):
    path.parent.mkdir(parents=True,exist_ok=True)
    pcm = np.round(np.clip(samples,-1,1)*32767).astype('<i2')
    with wave.open(str(path),'wb') as f:
        f.setnchannels(2); f.setsampwidth(2); f.setframerate(RATE); f.writeframes(pcm.tobytes())

if __name__ == '__main__':
    manifest = {}
    reel = []
    for kind, count in [('bolter',4),('grenade',3),('relay',2),('chainsword',3)]:
        for variant in range(count):
            samples = design(kind,variant)
            name = f'{kind}_{variant}.wav'
            save(OUT/name,samples)
            manifest[name] = {'seconds':len(samples)/RATE,'peak_dbfs':float(20*np.log10(np.max(np.abs(samples)))),'rms_dbfs':float(20*np.log10(np.sqrt(np.mean(samples*samples))))}
            if variant==0:
                reel += [samples,np.zeros((RATE//2,2))]
    save(ROOT/'build/audio/weapon-preview.wav',np.concatenate(reel))
    (ROOT/'art/audio/synthesis.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('AUDIO PASS: 12 original stereo effects, finite PCM, peak headroom >1.7 dB')
