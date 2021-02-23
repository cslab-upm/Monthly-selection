# Llamada: python3 random_selection.py dia_inicio dia_final nombre_directorio
# Los días deberán ir en formato: año-mes-dia.
# "nombre_directorio" es el nombre que tendrá el directorio que contenga los 
# ficheros de sonido y las imágenes asociadas. El convenio recomendado es:
# año_mes.
# Ejemplo: python3 random_selection.py 2020-05-01 2020-05-31 2020_05

import pandas as pd
import numpy as np

from pyo import *
import time

import matplotlib.pyplot as plt
import librosa
import librosa.display

import subprocess
import os

import urllib.request
import sys

import configparser

#------ Parámetros ------
try:
    config = configparser.ConfigParser()
    config.read('configuracion.properties')
    
    # Número de muestras de cada uno de los tipos de ecos
    s = int(config.get('Seleccion', 's')) # Cortos
    m = int(config.get('Seleccion', 'm')) # Duración intermedia
    l = int(config.get('Seleccion', 'l')) # Largos
    # Duración en milisegundos de los límites entre los distintos tipo de ecos:
    # Ecos cortos: < t_l. t_l <= Ecos de duración intermedis < t_h. t_h <= Ecos largos
    t_l = int(config.get('Seleccion', 't_l'))
    t_h = int(config.get('Seleccion', 't_h'))
    
    # Parámetros para la generación del sonido.
    #Parámetros para el volumen
    Med_1 = float(config.get('Sonidos', 'Med_1'))  # Valor medio
    Amp_1 = float(config.get('Sonidos', 'Amp_1'))  # Amplitud
    #Parámetros para el tono
    Med_2 = float(config.get('Sonidos', 'Med_2'))  # Valor medio
    Amp_2 = float(config.get('Sonidos', 'Amp_2'))  # Amplitud
    # Parámetros básicos del sonido
    basic_freq = [261.6, 523.2, 1046.4] 
    basic_mul = [.3, .3*.9, .3*.5] 
    
    # Mes y año extraido. Será el nombre de la carpeta con los sonidos.
    month = sys.argv[3]
    
    # URL del servidor.
    server_url = config.get('URL', 'server_url')
    
    # URL de la descarga del fichero con las muestras.
    file_url = config.get('URL', 'download_file_url_1') + sys.argv[1] + config.get('URL', 'download_file_url_2') + sys.argv[2] + config.get('URL', 'download_file_url_3')
    
    # Dirección y nombre del fichero temporal con las muestras
    data_file_path = config.get('Directorios', 'data_file_path')
    # Dirección del directorio "detecciones".
    detecciones_path = config.get('Directorios', 'detecciones_path')
    # Dirección del directorio "opendata".
    open_data_path = detecciones_path + config.get('Directorios', 'open_data_rel_path')
    # Dirección del directorio en el que se guardarán los sonidos.
    sounds_path =  open_data_path + config.get('Directorios', 'sounds_rel_path') + month +'/'
    
    # Cabecera para la generación de sonidos
    sounds_headers = ['date', 'time', 'frequency', 'data']
    # Cabecera para el fichero de la API
    API_headers = ['ID','DATE','STATION','DURATION','lnk_fits','lnk_votsp','lnk_spec','lnk_csvsp','lnk_votlc','lnk_lc','lnk_csvlc','lnk_snd']
    # Cabecera para los manifest de Zooniverse
    manifest_sounds_header = ['id','snd','pic']
    manifest_images_header = ['id','lc','sp']
    
except:
    print('ERROR: No se ha podido leer el fichero de configuración.')
    sys.exit(1)

#------ Funciones ------
def sonification(file_path, destination_path, sample_ID):
    try:
        path_file = destination_path + sample_ID + ".wav"
        
        var_1 = []  # La variable correspondiente a la curva de luz
        var_2 = []  # La variable correspondiente al efecto Doppler en el espectrograma
        
        data = pd.read_csv(file_path, header=None, names=sounds_headers)
        
        # Extracción, a partir del fichero del espectrograma los valores de la
        # curva de luz y el espectrograma relevantes.
        for t in data['time'].unique():
            var_1.append(data[data['time']==t]['data'].max())
            
        
        for t in data['time'].unique():
            l = len(data[data['time']==t]['data'])
            var_2.append(data[data['time']==t]['data'].iloc[int(l*3/8):int(l*5/8)].sum()/len(data[data['time']==t]['data'].iloc[int(l*3/8):int(l*5/8)]))
        
        
        # Normalización de los cambios de frecuencia y volumen según los 
        # parámetros establecidos al principio del programa.
        M_1 = max(var_1)
        m_1 = min(var_1)
        if M_1 != m_1:
            a_1 = 2 / (M_1 - m_1)
            b_1 = 1 - 2 * M_1 / (M_1 - m_1)
        else:
            a_1 = 0
            b_1 = 0
            
        M_2 = max(var_2)
        m_2 = min(var_2)
        if M_2 != m_2:
            a_2 = 2 / (M_2 - m_2)
            b_2 = 1 - 2 * M_2 / (M_2 - m_2)
        else:
            a_2 = 0
            b_2 = 0
            
       
        # Creación de las variables normalizadas que se utilizarán para generar
        # los sonidos. La variable 1 se corresponde con la amplitud y la
        # variable 2 con la frecuencia.
        var_1_normalized = [Med_1 + Amp_1 * (a_1 * i + b_1) for i in var_1]
        var_2_normalized = [Med_2 + Amp_2 * (a_2 * i + b_2) for i in var_2]
        
        
        inst_freq = [f * var_2_normalized[0] for f in basic_freq]
        inst_mul = [m * var_1_normalized[0] for m in basic_mul]
        
        # Inicio del servidor para generar el sonido.
        s = Server().boot()
        s.start()
            
        # Inicio del proceso de generación del sonido.
        sin = Sine(freq=inst_freq, mul=inst_mul)
        h1 = Harmonizer(sin).out()
        
        brec = Record(h1, filename=path_file, chnls=2, fileformat=0, sampletype=0)
        clean = Clean_objects(0, brec)
        
        time.sleep(0.1)
        
        for i in range(0,len(var_1_normalized)):
            inst_freq = [f * var_2_normalized[i] for f in basic_freq]
            inst_mul = [m * var_1_normalized[i] for m in basic_mul]
            sin.set(attr="freq", value=inst_freq, port=0.05)
            sin.set(attr="mul", value=inst_mul, port=0.05)    
            time.sleep(0.1)
            
        clean.start()
        s.stop()
        
        return path_file
    except:
        print('ERROR: No se ha podido generar el sonido para fichero ' + file_path)
        return 'Error' + path_file

def image_from_sound(file_path, destination_path, sample_ID):
    # Función que genera una imagen a partir de un fichero de sonido.
    try:
        path_file = destination_path + sample_ID + ".png"

        # Extracción de la información del fichero de sonido.
        x, sr = librosa.load(file_path, sr=44100)

        fig = plt.figure(figsize=(14, 8))        
        
        X = librosa.stft(x)
        Xdb = librosa.amplitude_to_db(abs(X))
        ax_down = fig.add_subplot(212)
        ax_down.tick_params(axis="y",direction="in", pad=-55)
        ax_down.yaxis.label.set_visible(False)
        ax_down.tick_params(axis='y', colors='white')
        librosa.display.specshow(Xdb, sr=sr, x_axis='time', y_axis='log')
        labels = ['0 Hz', '64 Hz', '128 Hz', '256 Hz', '512 Hz', '1024 Hz', '2048 Hz', '4096 Hz', '8192 Hz', '16384 Hz']
        ax_down.set_yticklabels(labels)
        
        plt.xlabel('Time (s)')
        plt.savefig(path_file,bbox_inches='tight')
        fig.clear()
        plt.close(fig)
        return path_file
    except:
        print('ERROR: No se ha podido generar la imagen de ' + file_path)
        return 'Error' + path_file
    
def wav_to_mp3(wav):
    # Función que convierte el fichero de sonido de .wav a .mp3 y borra el 
    # original. El formato es necesario que sea mp3 ya que Zooniverse no admite 
    # .wav, sin embargo, la librería pyo no permite generar los ficheros en
    # este formato.
    try:
        cmd = 'lame --preset insane %s' % wav
        subprocess.call(cmd, shell=True)
        os.remove(wav)
        return wav[:-3] + 'mp3'
    except:
        print('ERROR: No se ha podido convertir a mp3 el fichero ' + wav)
        return 'Error' +  wav[:-3] + 'mp3'

#-------------- Comienzo del programa --------------
# Desrcarga del fichero con las muestras de ecos.
urllib.request.urlretrieve(file_url, data_file_path)
# Carga de los datos de los ecos en un Data Frame.
data = pd.read_csv(data_file_path,index_col='#n')
# Eliminación
os.remove(data_file_path)

# Creación, si no existe, del directorio en el que se guardarán los sonidos.
if not os.path.exists(sounds_path):
    os.makedirs(sounds_path)

# Se dividen todas las muestras en tres Data Frames según las duraciones de los parámetros.
data_s = data[data['DURATION'] < t_l]
data_m = data[data['DURATION'] > t_l]
data_m = data_m[data_m['DURATION'] < t_h]
data_l = data[data['DURATION'] > t_h]

# Se comprueba que hay suficientes muestras de cada tipo y, en case de que no las
# haya, las restantes se añaden al tipo de menor duración.  
if len(data_l) < l:
    m += l - len(data_l)
    l = len(data_l)
    
if len(data_m) < m:
    s += m - len(data_m) 
    m = len(data_m) 
    
if len(data_s) < s:
    s = len(data_s)

# Se crea un Data Frame con una selección aleatoria lo más homogénea posible
# según la duración.
data_selection = pd.concat([data_s.sample(s),data_m.sample(m),data_l.sample(l)])

# Listas que se usarán para añadir la información (la URL) de los nuevos
# archivos que se van a crear: sonidos (mp3) y la imagen del sonido (png).
lnk_snd = []
lnk_sndpic = []

# Listas para crear los "manifest" necesarios para subir las muestras a Zooniverse.
manifest_sounds = []
manifest_images = []


for index, sample in data_selection.iterrows():
    
    # Generación del sonido
    sample_sound_path = sonification(detecciones_path + sample['lnk_csvsp'].split(server_url)[1], sounds_path, sample['ID'])

    # Generación de la imagen del sonido
    if sample_sound_path != -1:
        sample_image_path = image_from_sound(sample_sound_path, sounds_path, sample['ID']) 
        lnk_sndpic.append(server_url + sample_image_path.split(detecciones_path)[1])
    
        # Conversión del fichero .wav en .mp3
        sample_sound_path = wav_to_mp3(sample_sound_path)
        lnk_snd.append(server_url + sample_sound_path.split(detecciones_path)[1])
    
    # Se añade la ubicación de los nuevos ficheros a las listas de los "manifest".
    manifest_sounds.append([sample['ID'], sample_sound_path, sample_image_path])
    manifest_images.append([sample['ID'], detecciones_path + sample['lnk_lc'].split(server_url)[1], detecciones_path + sample['lnk_spec'].split(server_url)[1]])
    
    
# Se añade en el Data Frame las URL de los sonidos y sus imágenes.
data_selection["lnk_snd"] = lnk_snd
data_selection["lnk_sndpic"] = lnk_sndpic

# Guardado (previa conversión en Data Frame) del "manifest" para la clasificación
# mediante sonidos (sonido e imagen asociada).
manifest_sounds= pd.DataFrame(manifest_sounds)
manifest_sounds.to_csv("./manifest_files/manifest_sounds_" + month +".csv", header=manifest_sounds_header, index=False)

# Guardado (previa conversión en Data Frame) del "manifest" para la clasificación
# mediante imágenes (curva de luz y espectrograma).
manifest_images= pd.DataFrame(manifest_images)
manifest_images.to_csv("./manifest_files/manifest_images_" + month +".csv", header=manifest_images_header, index=False)

# Guardado del fichero necesario para subir nuevas muestras a la API.
data_selection[API_headers].to_csv("./API_files/API_new_samples_" + month +".csv", index=False)
