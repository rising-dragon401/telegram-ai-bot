from elevenlabs import clone, generate, play, set_api_key
from elevenlabs.api import History, Voices
import os
from dotenv import load_dotenv
load_dotenv()


set_api_key(os.getenv("ELEVEN_LABS_API_KEY"))


def generate_voice(creator_display_name, message, email='', language=''):
  name_to_use = creator_display_name

  if language and language.lower() != 'english':
    name_to_use = creator_display_name + '-spanish'
    print('using spanish?!')

  voices = Voices.from_api()
  
  # find voice using display_name
  voice = None
  for voice in voices:
    if voice.name == name_to_use:
      break

  
  voice.settings.stability = 0.3
  voice.settings.similarity_boost = 0.7

  audio = generate(message, voice=voice, model='eleven_multilingual_v1')
  
  return audio


  
