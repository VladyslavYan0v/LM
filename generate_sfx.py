import wave
import math
import struct
import os

def generate_sfx(filename, frequency=440.0, duration=0.1, volume=0.5, waveform="square", sample_rate=44100):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        total_samples = int(sample_rate * duration)
        for i in range(total_samples):
            t = i / sample_rate
            envelope = max(0.0, 1.0 - (i / total_samples))
            
            if waveform == "square":
                val = 1.0 if math.sin(2.0 * math.pi * frequency * t) > 0 else -1.0
            elif waveform == "sawtooth":
                val = 2.0 * (t * frequency - math.floor(0.5 + t * frequency))
            else:
                val = math.sin(2.0 * math.pi * frequency * t)
            
            value = int(volume * envelope * val * 32767.0)
            wav_file.writeframesraw(struct.pack('<h', value))
            
    print(f"Generated {filename}")

if __name__ == "__main__":
    generate_sfx("embed/sfx/voice_blue.wav", frequency=380.0, duration=0.06, waveform="sine", volume=0.3)
    generate_sfx("embed/sfx/voice_red.wav", frequency=95.0, duration=0.08, waveform="sawtooth", volume=0.4)
    generate_sfx("embed/sfx/click.wav", frequency=800.0, duration=0.02, waveform="square", volume=0.3)
    generate_sfx("embed/sfx/error.wav", frequency=150.0, duration=0.15, waveform="sawtooth", volume=0.3)