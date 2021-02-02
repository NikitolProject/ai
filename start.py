import os
import time
import datetime
import asyncio

import requests
import dialogflow
import wikipedia
import pyttsx3

import speech_recognition as sr
import simpleaudio as sa

from translate import Translator
from playsound import playsound
from fuzzywuzzy import fuzz


cmd = {
    'determine': ["Я смогла решить Ваш пример.", "Вот ответ на Ваш пример, надеюсь, я Вам помогла.",
                  "Держите ответ на Ваш пример!"],
    'search': ["Вот, что я смогла найти.", "Надеюсь, этот ответ Вам смог помочь.",
               "Это то, что я смогла найти по Вашему вопросу."],
    'time':  ["Сейчас", "Уже", "На часах", "На данный момент"],
    'translate': ['Вот, как я смогла перевести на', 'Этот текст был переведён по Вашей просьбе на', 
                  'Я смогла перевести этот текст на']
}


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'small-talk-cmng-d9902e2a00a1.json'

DIALOGFLOW_PROJECT_ID = 'small-talk-cmng'
DIALOGFLOW_LANGUAGE_CODE = 'ru'
SESSION_ID = 'me'


async def send_request(text) -> any:
    return requests.post(url='https://unitools.tech/api/sp_syn', data={
        'text': text,
        'audio_format': 'mp3',
        'name': 'Cate',
        'token': '03AGdBq27bzf_3DQGuShxBjP-EVjOWoGkuc1Wgk2aeRDXwH1iMqNqn7bg774V_JmLnB4bcSsB0KK7eBz9KJIIo_7lnNVv38SIfrrV'
                 'g2T9iADRRe0hclHJ2n0JTSJBlBZXFSEqNGQWd5dSdpCnnq25S4xXSLjyaEciYi4H-g8JUjjlr6Qm6aPLOQoEm0F1JaLPVTlajNmNR'
                 'DF0m55U4KeEBMkZtU-7cToBTqOifcDYrZ3imChd2Bu6s2eYvdRuES_eBAJGvoOmtOwHMC92aetAhSg5SI9VFBu5AWwEOej5_uIK5s'
                 'NDUaTkKabqmHqzHYlNvt6E1Ux2RS--vnIZ5nn7sg_A-yRGQYEWAk_k1lxZvHAsmiPuOI-PAqmJ55rtpnO05IB74ZzgmZGDtjLZcRZ'
                 'FkePdB8FmZnG-yRdasI8LVMwnR8x1LjcH-fG0'
    })


async def get_audio(text) -> any:
    response: any = await send_request(text)
    resp: list = str(response.content).split("'")
    response: any = requests.get(f'https://unitools.tech{resp[1]}')
    return response


async def play_audio(text) -> any:
    response: any = await get_audio(text)
    with open('song.mp3', 'wb') as file:
        file.write(response.content)
    playsound("song.mp3")


async def main(words):
  session_client = dialogflow.SessionsClient()
  session = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)
  text_input = dialogflow.types.TextInput(text=words, language_code=DIALOGFLOW_LANGUAGE_CODE)
  query_input = dialogflow.types.QueryInput(text=text_input)
  try:
      response = session_client.detect_intent(session=session, query_input=query_input)
  except Exception as e:
      raise play_audio(f"Ошибка распознание текста: {e}")

  for x in cmd['translate']:
      if response.query_result.fulfillment_text == x:
        translator = Translator(from_lang="Russian", to_lang="English")
        lang = translator.translate(response.query_result.parameters.fields['language'].string_value)
        if response.query_result.parameters.fields['language-from'].string_value != '':
            lang_from = translator.translate(response.query_result.parameters.fields['language-from'].string_value)
        else:
            lang_from = "Russian"
        translator = Translator(from_lang=lang_from, to_lang=lang)
        text = translator.translate(response.query_result.parameters.fields['any'].string_value)
        print(f"Перевод: {text}")
      
  for x in cmd['determine']:
      if response.query_result.fulfillment_text == x:
          print(f"Ответ: {eval(response.query_result.parameters.fields['any'].string_value)}")

  for x in cmd['search']:
      if response.query_result.fulfillment_text == x:
          link = response.query_result.parameters.fields['any'].string_value
          wikipedia.set_lang("ru")
          result = str(wikipedia.summary(link, sentences=1))
          print(f"Ответ: {result}")

  for x in cmd['time']:
      if response.query_result.fulfillment_text == x:
          now = datetime.datetime.now()
          response.query_result.fulfillment_text = f"{response.query_result.fulfillment_text} {now.strftime('%H:%M')}"

  await play_audio(response.query_result.fulfillment_text)

 
async def callback(recognizer, audio):
    try:
        voice = recognizer.recognize_google(audio, language = "ru-RU").lower()
        print(f"[log] Распознано: {voice}")

        await main(voice)
 
    except sr.UnknownValueError:
        print("[log] Голос не распознан!")

    except sr.RequestError as e:
        print(f"[log] Ошибка: {e}")


async def start_va():
    r = sr.Recognizer()
    m = sr.Microphone()
    
    with m as source:
        r.adjust_for_ambient_noise(source)
    
    stop_listening = r.listen_in_background(m, callback)
    while True: time.sleep(0.1)


loop = asyncio.get_event_loop()
loop.create_task(start_va())
loop.run_forever()