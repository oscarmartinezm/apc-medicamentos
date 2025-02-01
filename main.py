import openai
import csv
import json
import configparser
import time
import os

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

# Function to get the active principle of a medication
def get_active_principle(medication):
  global MEDICAMIENTOS_DICT, client
  # Check if medication is already cached
  if medication in MEDICAMIENTOS_DICT:
    return MEDICAMIENTOS_DICT[medication]
  prompt = f'For the pharmaceutical medication {medication}, provide its active principle, providing only the name, with no any other text.'
  try:
    response = client.chat.completions.create(
      model='gpt-3.5-turbo-1106',
      messages=[{'role': 'user', 'content': prompt}],
      temperature=0.7
    )
    active_principle = response.choices[0].message.content.strip()
    # Save to JSON cache for future use
    MEDICAMIENTOS_DICT[medication] = active_principle
    save_cache(CACHE, MEDICAMIENTOS_DICT)
    return active_principle
  except Exception as e:
    print(f'Error with {medication}: {e}')
    MEDICAMIENTOS_DICT[medication] = 'Error'
    save_cache(CACHE, MEDICAMIENTOS_DICT)
    return 'Error'

def get_atc_code(active_principle):
  global MEDICAMIENTOS_ATC_DICT, client
  # Check if medication is already cached
  if active_principle in MEDICAMIENTOS_ATC_DICT:
    return MEDICAMIENTOS_ATC_DICT[active_principle]
  prompt = f'For the active principle {active_principle}, provide its ATC code and its description in spanish, providing only the values with no any other text, following this format "atc | description".'
  try:
    response = client.chat.completions.create(
      model='gpt-3.5-turbo-1106',
      messages=[{'role': 'user', 'content': prompt}],
      temperature=0.7
    )
    atc_code = response.choices[0].message.content.strip()
    # Save to JSON cache for future use
    MEDICAMIENTOS_ATC_DICT[active_principle] = atc_code
    save_cache(CACHE_ATC, MEDICAMIENTOS_ATC_DICT)
    return atc_code
  except Exception as e:
    print(f'Error with {active_principle}: {e}')
    MEDICAMIENTOS_ATC_DICT[active_principle] = 'Error'
    save_cache(CACHE_ATC, MEDICAMIENTOS_ATC_DICT)
    return 'Error'

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
      # Get the ATC code (from API or JSON cache)
      atc_code = get_atc_code(active_principle)
      # Add to RESULTS list
      RESULTS.append({
        'Articulo_Id': medication_id,
        'Articulo_Nombre': medication_name,
        'Principio_Activo': active_principle,
        'ATC': atc_code.split('|')[0].strip() if '|' in atc_code else '',
        'ATC_Descripcion': atc_code.split('|')[1].strip() if '|' in atc_code else ''
      })
      # Small delay to avoid API rate limits
      time.sleep(1)
  save_csv()
  print(f'Process completed. CSV file generated: {OUTPUT_CSV}')

main()