import openai
import csv
import json
import configparser
import time
import os
import sys

# File names
INPUT_CSV = 'medicamentos.csv'
OUTPUT_CSV = 'medicamentos-nuevo.csv'
CACHE = 'medicamentos-cache.json'
CACHE_ATC = 'medicamentos-cache-atc.json'

RESULTS = []
MEDICAMIENTOS_DICT = {}
MEDICAMIENTOS_ATC_DICT = {}

# Load API Key from config file
config = configparser.ConfigParser()
config.read('config.ini')
API_KEY = config['OPENAI']['API_KEY']

# Create OpenAI client
client = openai.OpenAI(api_key=API_KEY)

def load_cache():
  global MEDICAMIENTOS_DICT, MEDICAMIENTOS_ATC_DICT
  # Load cached data from JSON (if it exists)
  if os.path.exists(CACHE):
    with open(CACHE, 'r', encoding='utf-8') as json_file:
      MEDICAMIENTOS_DICT = json.load(json_file)
  else:
    MEDICAMIENTOS_DICT = {}
  # Load cached data from JSON (if it exists)
  if os.path.exists(CACHE_ATC):
    with open(CACHE_ATC, 'r', encoding='utf-8') as json_file:
      MEDICAMIENTOS_ATC_DICT = json.load(json_file)
  else:
    MEDICAMIENTOS_ATC_DICT = {}

def save_cache(file, data):
  # Save updated JSON cache
  with open(file, 'w', encoding='utf-8') as json_file:
    json.dump(data, json_file, indent=2, ensure_ascii=False)

def execute_prompt(prompt):
  global client
  try:
    response = client.chat.completions.create(
      model='gpt-4o',
      messages=[{'role': 'user', 'content': prompt}],
      temperature=0.7
    )
    return response.choices[0].message.content.strip()
  except Exception as e:
    print(f'Error with {prompt}: {e}')
    return 'Error'

# Function to get the active principle of a medication
def get_active_principle(medication):
  medication = 'Xirmen 8mg'
  global MEDICAMIENTOS_DICT
  # Check if medication is already cached
  #if medication in MEDICAMIENTOS_DICT:
  #  return MEDICAMIENTOS_DICT[medication]
  prompt = f'Para el medicamento farmaceútico {medication}, dame su principio activo, proveyendo solo el nombre, sin ningún otro texto.'
  prompt = '¿Cuál es el nombre base del medicamento ALERXY SPRAY NASAL 140DOSIS?'
  result = execute_prompt(prompt)
  # Save the result in the cache
  MEDICAMIENTOS_DICT[medication] = result
  print(prompt)
  print(result)
  save_cache(CACHE, MEDICAMIENTOS_DICT)
  return result

def get_atc_code(active_principle):
  global MEDICAMIENTOS_ATC_DICT
  # Check if medication is already cached
  if active_principle in MEDICAMIENTOS_ATC_DICT:
    return MEDICAMIENTOS_ATC_DICT[active_principle]
  prompt = f'Para el principio activo {active_principle}, proporciona su código ATC y su descripción, brindando solo los valores sin ningún otro texto, siguiendo este formato: "atc | descripción".'
  result = execute_prompt(prompt)
  # Save the result in the cache
  MEDICAMIENTOS_ATC_DICT[active_principle] = result
  save_cache(CACHE_ATC, MEDICAMIENTOS_ATC_DICT)
  return result

def save_csv():
  global RESULTS
  # Save the new CSV file with ';' delimiter
  with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as file:
    fieldnames = ['Articulo_Id', 'Articulo_Nombre', 'Principio_Activo', 'ATC', 'ATC_Descripcion']
    writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=';')
    # Write header
    writer.writeheader()
    # Write data
    writer.writerows(RESULTS)

def main():
  global INPUT_CSV, RESULTS
  count = 0
  load_cache()
  # Read the original CSV file with ';' delimiter
  with open(INPUT_CSV, mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file, delimiter=';')
    for row in reader:
      count += 1
      medication_id = row['Articulo_Id']
      medication_name = row['Articulo_Nombre'].strip()
      print(f'Processing #{count}: {medication_name}')
      # Get the active principle (from API or JSON cache)
      active_principle = get_active_principle(medication_name)
      sys.exit()
      # Get the ATC code (from API or JSON cache)
      atc_code_info = get_atc_code(active_principle)
      if ('Error' not in atc_code_info):
        atc_code = atc_code_info.split('|')[0].strip()[:3] if '|' in atc_code else ''
        atc_description = atc_code_info.split('|')[1].strip() if '|' in atc_code else ''
      else:
        atc_code = ''
        atc_description = 'Error'
      # Add to RESULTS list
      RESULTS.append({
        'Articulo_Id': medication_id,
        'Articulo_Nombre': medication_name,
        'Principio_Activo': active_principle,
        'ATC': atc_code,
        'ATC_Descripcion': atc_description
      })
      # Small delay to avoid API rate limits
      time.sleep(1)
  save_csv()
  print(f'Process completed. CSV file generated: {OUTPUT_CSV}')

main()