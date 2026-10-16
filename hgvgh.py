import math
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
import sounddevice as sd



# --- 0. Настройка параметров + чтение файла ---

SAMPLE_RATE = 44100  # Частота дискретизации (Гц)
TEMPO = 120  # Темп (ударов в минуту)
BEAT_DURATION = 60 / TEMPO  # Длительность одной четвертной ноты

# Словарь частот нот первой и второй октавы (в Герцах)
NOTES = {
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23,
    'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
    'C5': 523.25, 'REST': 0
}
# Словарь чего-то для расшифровки фпйла
tabl = {
    'A': 9, 'A#': 10, 'B': 11,
    'C': 0, 'C#': 1, 'D': 2,
    'D#': 3, 'E': 4, 'F': 5,
    'F#': 6, 'G': 7, 'G#': 8,
    'РЎ': 0
}

# ------------------------------------------------------
def durat (razmernoti, bpm, delitel):
    dln=(((60*delitel)/bpm)/razmernoti)*1000
    return dln
# ------------------------------------------------------
def hz (vnutri, snaruzi):
    i= snaruzi*12 + tabl[vnutri]
    gerz=440*(2**((i-57)/12))
    return gerz
# ------------------------------------------------------

# --- 1. Выбор режима ---
mode_0 = int(input(f'simple test (0) | file run (1)\n--->'))
if mode_0 == 1:
    file = open(str(input('file\'s name, pls\n--->')))
    temp, raz = map(int, file.readline().rstrip('\n')[:-2].split())
    sound_smth = []
    for line in file:
        stroka = line.rstrip('\n')
        nota, octava, dlit = stroka.split()
        octava = int(octava)
        dlit = float(dlit)
        a = hz(nota, octava)
        b = round(durat(dlit,temp,raz))
        sound_smth.append((a,b/1000))
mode  = int(input('wave\'s modes:\nsin = 1\ncos = 2\nsaw = 3\nsquare = 4\ntriangle = 5\n--->'))

def square(array):
    new_array = []
    for element in array:
        new_array.append(2*(element-np.floor(element + 0.5)))
    return new_array


# --- 2. Функция генерации звука одной ноты ---
def generate_note(frequency, duration, sample_rate=SAMPLE_RATE):
    num_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, num_samples, endpoint=False)

    if frequency == 0:
        return np.zeros(num_samples)

    # -----------------------------------------------------------------------------------------------
    x = 2 * np.pi * frequency * t
    if mode == 1: wave = np.sin(x)
    elif mode == 2: wave = np.cos(x)
    elif mode == 3: wave = square(x/8)
    elif mode == 4: wave = np.sign(np.sin(x))
    elif mode == 5: wave = (2 / math.pi) * np.arcsin(np.sin(x))


    # Плавное нарастание и затухание (ADSR-огибающая)
    attack_samples = int(sample_rate * 0.05)
    release_samples = int(sample_rate * 0.05)

    envelope = np.ones(num_samples)
    if num_samples > (attack_samples + release_samples):
        envelope[:attack_samples] = np.linspace(0, 1, attack_samples)
        envelope[-release_samples:] = np.linspace(1, 0, release_samples)
    else:
        envelope = np.linspace(1, 0, num_samples)

    return wave * envelope


# --- 3. Функция сборки мелодии ---
def create_melody(melody_score, sample_rate=SAMPLE_RATE):
    full_track = np.array([], dtype=np.float32)

    for note_name, beats in melody_score:
        if mode_0 == 1:
            duration = beats
            freq = note_name
        else:
            duration = beats * BEAT_DURATION
            freq = NOTES.get(note_name, 0)

        note_wave = generate_note(freq, duration, sample_rate)
        full_track = np.concatenate((full_track, note_wave))

    return full_track


# --- 4. Основной блок выполнения ---
if __name__ == "__main__":
    if mode_0 == 1:
        my_song = sound_smth
    else:
        my_song = [
        ('C4', 1.0), ('G4', 1.0), ('G4', 1.0), ('A4', 1.0), ('G4', 2.0),
        ('REST', 0.5),
        ('B4', 1.0), ('C5', 1.0)
    ]

    print("Генерируем мелодию...")
    audio_data = create_melody(my_song)

    # Нормализация громкости
    audio_data = audio_data / np.max(np.abs(audio_data))

    # -------------------------------------------------------------
    # --- НОВЫЙ БЛОК: Воспроизведение звука динамиков через Python ---
    # -------------------------------------------------------------
    print("Воспроизводим мелодию...")
    sd.play(audio_data, SAMPLE_RATE)
    sd.wait()  # Ожидаем окончания проигрывания перед выполнением следующего кода
    print("Воспроизведение завершено!")
    # -------------------------------------------------------------

    # Сохранение в WAV-файл (формат 16-бит PCM)
    audio_int16 = (audio_data * 32767).astype(np.int16)
    output_filename = "melody.wav"
    wavfile.write(output_filename, SAMPLE_RATE, audio_int16)
    print(f"Мелодия сохранена в файл: {output_filename}")
    print("Строим график осциллограммы...")

    plt.figure(figsize=(12, 6))
    zoom_samples = int(SAMPLE_RATE * 0.5)
    plt.subplot(2, 1, 1)
    plt.plot(np.linspace(0, 0.5, zoom_samples), audio_data[:zoom_samples], color="b")
    plt.xlabel("Время (с)")
    plt.ylabel("Амплитуда")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.title("Осциллограмма сгенерированной мелодии (фрагмент)")

    plt.subplot(2, 1, 2)
    samples_to_show = min(len(audio_data), int(SAMPLE_RATE * 0.05))
    time_axis = (np.arange(samples_to_show) / SAMPLE_RATE * 1000)
    plt.plot(time_axis, audio_data[:samples_to_show], color="navy")
    plt.xlabel("Время (мс)")
    plt.ylabel("Амплитуда")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.title("Фрагмент волны")

    plt.tight_layout()
    plt.savefig("waveform.png", dpi=300)
    plt.show()
    print("График сохранен в файл: waveform.png")
