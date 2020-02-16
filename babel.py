import os
import logging
import requests
import time
from xml.etree import ElementTree
from aiy.board import Board, Led
from aiy.voice import audio
from aiy.cloudspeech import CloudSpeechClient

#Azure
SUBSCRIPTION_KEY = "7134fbbe2a3d4485ad9280f895bfa37f"
TIME_STRING = time.strftime("%Y%m%d-%H%M")
ACCESS_TOKEN = None
SAVE_STRING = ""

#Transcription
API_KEY = 'trnsl.1.1.20200215T092345Z.92ff7209205a701f.cae85a5006bdbe8ff9ac5ec0b50a40ddee011936'
ENDPOINT_URL= 'https://translate.yandex.net/api/v1.5/tr.json/translate'

#Dynamics
BUTTON_PRESSED = False


###
def translate(input_text, input_language, output_language):
    language_direction = '%s-%s' % (input_language, output_language)
    translation_params = dict(key = API_KEY, text=input_text, lang = language_direction)
    result = requests.get(ENDPOINT_URL, translation_params)
    print('result')
    print(result)
    output = eval(result.text)['text']
    if type(output) is list:
        return output[0]
    else:
        return output
###


def get_token():
    global ACCESS_TOKEN
    fetch_token_url = "https://westus.api.cognitive.microsoft.com/sts/v1.0/issueToken"
    headers = {'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY}
    response = requests.post(fetch_token_url, headers=headers)
    ACCESS_TOKEN = str(response.text)

def save_audio(input_string, code, code_list):
    global ACCESS_TOKEN
    global SAVE_STRING
    base_url = 'https://westus.tts.speech.microsoft.com/'
    path = 'cognitiveservices/v1'
    constructed_url = base_url + path
    headers = {
        'Authorization': 'Bearer ' + ACCESS_TOKEN,
        'Content-Type': 'application/ssml+xml',
        'X-Microsoft-OutputFormat': 'riff-24khz-16bit-mono-pcm',
        'User-Agent': 'TreeHacks'
    }
    xml_body = ElementTree.Element('speak', version='1.0')
    xml_body.set('{http://www.w3.org/XML/1998/namespace}lang', code)
    voice = ElementTree.SubElement(xml_body, 'voice')
    voice.set('{http://www.w3.org/XML/1998/namespace}lang', code)
    voice.set(
        'name', 'Microsoft Server Speech Text to Speech Voice ' + code_list)
    voice.text = input_string
    print("xml")
    print(xml_body)
    body = ElementTree.tostring(xml_body)
    response = requests.post(constructed_url, headers=headers, data=body)
    if response.status_code == 200:
        SAVE_STRING = 'output.wav'#'sample-' + TIME_STRING + '.wav'
        with open(SAVE_STRING, 'wb') as audio_write:
            audio_write.write(response.content)
            print("\nStatus code: " + str(response.status_code) +
                  "\nYour TTS is ready for playback.\n")
    else:
        print("\nStatus code: " + str(response.status_code) +
              "\nSomething went wrong. Check your subscription key and headers.\n")
        print("Reason: " + str(response.reason))

def play_audio(text, code, code_list):
    save_audio(text, code, code_list)
    audio_format = audio.AudioFormat(sample_rate_hz = 24000, num_channels = 1, bytes_per_sample = 2)
    audio.play_raw(audio_format, 'output.wav')
    print("playing audio %s..." % (text))

def active_mode(client, from_language_code, to_language_code, code_list):
    global BUTTON_PRESSED
    original_button_status = BUTTON_PRESSED
    board.led.state = Led.ON
    def check_button_status():
        if original_button_status != BUTTON_PRESSED:
            print("button not pressed yet")
        else:
            print("button pressed")
        return original_button_status != BUTTON_PRESSED
    transcribed_text = client.recognize(language_code = from_language_code, test_func=check_button_status)
    board.led.state = Led.OFF
    if original_button_status is not BUTTON_PRESSED and BUTTON_PRESSED == True:
        return
    if transcribed_text is not None:
        logging.info('Spoken input: %s' % transcribed_text)
        translated_text = translate(transcribed_text, from_language_code[:2], to_language_code[:2])    

        if original_button_status is not BUTTON_PRESSED and BUTTON_PRESSED == True:
            return
        logging.info('Translated output: %s' % translated_text)
        play_audio(translated_text, to_language_code, code_list)

def main():
    global BUTTON_PRESSED
    # Init
    get_token()
    # Read in input language
    logging.basicConfig(level=logging.DEBUG)
    logging.info('Initializing')
    client = CloudSpeechClient()
    # Language settings
    first_language_code = 'en-US'
    second_language_code = 'ar-SA'
    first_speaker_code = '(en-US, ZiraRUS)'
    second_speaker_code = '(ar-SA, Naayf)'

    # Language options
    # American English
    #language_code = 'en-US'
    #speaker_code = '(en-US, ZiraRUS)'
    # Mexican Spanish
    #language_code = 'es-MX'
    #speaker_code = '(es-MX, Raul, Apollo)'
    # High German
    #language_code = 'de-DE'
    #speaker_code = '(de-DE, HeddaRUS)'
    # Saudi Arabian Arabic
    #language_code = 'ar-SA'
    #speaker_code = '(ar-SA, Naayf)'




    def switch_button():
        global BUTTON_PRESSED
        BUTTON_PRESSED = not BUTTON_PRESSED

    with Board() as board:
        board.button.when_released = switch_button
        board.button.when_pressed = switch_button
        while True:
            if BUTTON_PRESSED:
                print("should output in Spanish")
                active_mode(board, client, first_language_code, second_language_code, second_speaker_code)
               
            else:
                print("should output in English")
                active_mode(board, client, second_language_code, first_language_code, first_speaker_code)
                

if __name__ == '__main__':
    main()
