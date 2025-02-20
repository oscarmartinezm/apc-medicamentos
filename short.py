import os
import configparser
import json
import csv
import openai
import sys
import subprocess

# Configuración
TEXT_FILE = "assets/principios-activos.txt" # Nombre del archivo de texto de entrada
CACHE_FILE = "CACHE/CACHE-atc.json"         # Archivo JSON para almacenar la caché
CSV_FILE = "results/atcs.csv"               # Archivo de salida CSV

# Load API Key from config file
config = configparser.ConfigParser()
config.read('config.ini')
API_KEY = config['OPENAI']['API_KEY']

openai.api_key = API_KEY  # OpenAI API key

COUNT = 0

# Load CACHE from JSON file
if os.path.exists(CACHE_FILE):
  with open(CACHE_FILE, 'r', encoding='utf-8') as f:
    CACHE = json.load(f)
else:
  CACHE = {}

def get_atc_code(active_principle):
  '''Gets the ATC code from the CACHE or queries OpenAI API if not found.'''
  global COUNT
  COUNT += 1
  if ('/' in active_principle):
    active_principle = active_principle.split('/')[0].strip()
  elif ('+' in active_principle):
    active_principle = active_principle.split('+')[0].strip()
  if ('no aplica' in active_principle.lower()):
    return 'No Aplica'
  elif active_principle in CACHE:
    print(f'Using CACHE for: {active_principle} (#{COUNT})')
    return CACHE[active_principle].replace("\n", ' // ')
  print(f'Querying API for: {active_principle} (#{COUNT})')
  prompt = f'''
    Dame el codigo ATC principal (de 3 caracteres) del principio activo {active_principle}. Dame solo el código sin ningún otro texto.
    Si no logras encontrar el codigo ATC, por favor responde "No encontrado porque xxxxxxxx" seguido de una muy breve explicación de por qué no lo encontraste,
    se conciso con la respuesta no hace falta que respondas "lo siento", o "lo lamento", se breve y directo.'
  '''.replace('\n', ' ').strip()
  response = openai.chat.completions.create(
    model='gpt-4',
    messages=[
      {'role': 'system', 'content': 'You are a helpful assistant.'},
      {'role': 'user', 'content': prompt}
    ]
  )
  if response.choices:
    atc_code = response.choices[0].message.content.strip()
    CACHE[active_principle] = atc_code
    # Save CACHE after each query
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
      json.dump(CACHE, f, ensure_ascii=False, indent=2)
    return atc_code.replace("\n", ' // ')
  else:
    print(f'Error: No valid response from API for {active_principle}')
    return 'ERROR'

# Read input file and get ATC codes, preserving duplicates
results = []
with open(TEXT_FILE, 'r', encoding='utf-8') as file:
  for line in file:
    principle = line.strip()
    if principle:
      comments = ''
      atc_code = get_atc_code(principle)
      if ('No Aplica' in atc_code):
        comments = principle
        atc_code = 'N/A'
      elif (len(atc_code) > 15):
        comments = atc_code
        atc_code = 'No ATC'
      results.append([principle, atc_code, comments])

# Save results to CSV
with open(CSV_FILE, 'w', newline='', encoding='utf-8') as file:
  writer = csv.writer(file)
  writer.writerow(['Principio Activo', 'ATC', 'Comentarios'])
  writer.writerows(results)

#Execute command to open file
subprocess.run(['open', CSV_FILE])

print(f'Process completed. Results saved in {CSV_FILE}.')

print(f'Process completed. Results saved in {CSV_FILE}.')
