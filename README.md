# Programa

Este programa se encargan de obtener las muestras que se van a utilizar en Zooniverse y de generar los ficheros. 

Los pasos que realiza para ello son los siguientes:
1. Descarga del servidor ETSIDI un fichero csv con las muestras de ecos para el intervalo de tiempo deseado.
2. División de esas muestras en tres Data Frames según su duración y selección aleatoria del número deseado de cada una de ellas.
3. Para cada una de las muestras seleccionadas:
	3.1 Por medio de la librería Pyo genera el fichero .wav con su sonificación (función "sonification").
	3.2 Genera la imagen asociada al sonido que se aca de crear (función "image_from_sound").
	3.3 Convierte el fichero a formato .mp3 (función "wav_to_mp3"). Esto es necesario porque Zooniverse admite únicamente este formato para los Subject Sets, pero la librería Pyo no permite crear este tipo de ficheros.
	3.4 Añade la información relevante de la muestra a los ficheros que se utilizarán para la API y Zooniverse.
4. Guarda los ficheros .csv con la información del punto 3.4.

## Instalación

Para la correcta ejecución del software, es necesario instalar **python3** y ciertas librerías de python:

**Python**

    sudo apt-get install python3.7
    
    
**librosa**

    pip3 install librosa
    
**pyo**
    
    pip3 install pyo 
    
## random_selection

Este script se encarga de seleccionar las muestras que se presentarán para su clasificación en Zooniverse y en los chatbots, así como de crear, para los ecos escogidos, el fichero de sonido y su imagen asociada. Del mismo modo, crea los ficheros .csv necesarios para añadir las muestras al "subject set" de Zooniverse y a la API.

La sintaxis para ejecutar el script es la siguiente:

    python3 random_selection.py dia_inicio dia_final nombre_directorio
    							

Los días iniciales y finales tendrán el formato YYYY-MM-DD. "nombre_directorio" será, además del nombre del directorio en el que se guardarán los sonidos y las imágenes de las muestras seleccionadas, el nombre que tendrá el subject set de Zooniverse. Se recomienda usar como nombre del directorio el año y el número de mes del que se van a sacar las muestras, por ejemplo 2020.

Ejemplo de ejecución:

	python3 random_selection.py 2020-05-01 2020-05-31 2020_05
