import requests, os, time, pydub
from tkinter.filedialog import askopenfilename

# Settings for your API key and the base directory you want to load .txt files from
api_key = ""
base_directory = r'C:/'
folder_name = input("Enter a name for these translations to be grouped under: ")
log_file_name = "%s%s/%s_logs.txt" % (base_directory, folder_name, folder_name)
file_paths = []

jisho_API_URL = 'http://jisho.org/api/v1/search/words'
# -----------------------------------------------------------------

# Creates a base directory folder to store the mp3s and logs
def create_base_directory(base_directory, folder_name):

    download_directory = base_directory + folder_name

    if not os.path.exists(download_directory):
        os.makedirs(download_directory)

    print("Your stuff will be put in... " + download_directory)
    return download_directory


# Opens a file and puts the words to be retrieved into a list
def getwords():
    original_word_list = []

    name = askopenfilename(initialdir="C:/",
                           filetypes=(("Text File", "*.txt"), ("All Files", "*.*")),
                           title="Choose a file."
                           )
    f = open(name, encoding="utf8")

    for line in f.readlines():
        # Seems to handle encoding issues
        cleaned_line = line.replace('\ufeff', '')
        original_word_list.append(cleaned_line.rstrip())

    if original_word_list[0] == "" and len(original_word_list) < 2:
        print()
        raise ValueError("There doesn't seem to be any words listed in the file you selected! (" + name + ")")
    else:
        return original_word_list


def get_results(jisho_API_URL, word):
    params = dict(keyword = word)

    try:
        request = requests.get(jisho_API_URL, params)
    except ConnectionError:
        print("Can't connect to the Jisho API")
        raise

    response = request.json()

    try:
        english_trans_list = response['data'][0]['senses'][0]['english_definitions']
    except IndexError:
        english_trans_list = ['No translation available from Jisho API']

    return english_trans_list


def getmp3s(japanese_with_english_translation_dict):
    ultimate_dict = {}

    # go through each word in wordsList and try to grab the URL for the mp3 download
    for word, translated_word in japanese_with_english_translation_dict.items():

        params = {
            'key': api_key,
            'format': 'json',
            'action': 'standard-pronunciation',
            'word': word,
            'eng_word': translated_word
        }

        url = ('http://apifree.forvo.com/key/' + params['key'] + '/format/' + params['format'] + '/action/' +
               params['action'] + '/word/' + params['word'] + '/language/' + "ja" + '/limit/1')

        # try to grab URL - if it doesn't exist then carry on
        try:
            resp = requests.get(url)
        except ConnectionError:
            print("Can't connect to the Forvo API")
            raise

        # turn the API response item into a JSON format, then put the useful bit of that response into another variable

        data = resp.json()

        queried_data = data['items']

        num_of_responses = len(queried_data)

        # append word and URL info to a dictionary if the API returned useful information for this word
        if num_of_responses > 0:
            mp3link = queried_data[0]['pathmp3']
            ultimate_dict[word] = {
                'translated_word': translated_word,
                'mp3_URL': mp3link
            }
        else:
            ultimate_dict[word] = {
                'no_match_jap': True
            }

    return ultimate_dict


def merge_mp3s(mp3files, download_directory, folder_name):

    combined = pydub.AudioSegment.empty()

    for file in mp3files:
        sound = pydub.AudioSegment.from_mp3(file)
        combined += sound

    combined.export(download_directory + "/" + folder_name + ".mp3", format="mp3")


def download_mp3(word, mp3url, download_directory):
    mp3 = requests.get(mp3url)

    file_name = "%s.mp3" % (word)
    file_path = "%s/%s" % (download_directory, file_name)

    if not os.path.exists(download_directory):
        os.makedirs(download_directory)
    else:
        with open(file_path, "wb") as out:
            # we open a new mp3 file and we name it after the word we're downloading
            # the file is opened in write-binary mode
            out.write(mp3.content)

    return file_path


def normalize_audio(file_path):
    sound = pydub.AudioSegment.from_mp3(file_path)
    normalized_sound = match_target_amplitude(sound, -20.0)

    normalized_sound.export(file_path, format="mp3")


def match_target_amplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)


def create_log_files(ultimate_dict, logfilename, log_msg):
    logfile = open(logfilename, 'w+', encoding="utf8")

    for word, url in ultimate_dict.items():
        logfile.write("%s : %s\n" % (word, url))

    logfile.write("\n%s" % (log_msg))

def main():

    start_time = time.time()
    unsuccessful_words_list = []
    japanese_with_english_translation_dict = {}

    download_directory = create_base_directory(base_directory, folder_name)

    print("Requesting list of Japanese words...")
    original_word_list = getwords()

    print("Retrieving english translations...")
    for word in original_word_list:
        japanese_with_english_translation_dict[word] = (get_results(jisho_API_URL, word))

    print("Retrieving mp3 download links from Forvo...")
    ultimate_dict = getmp3s(japanese_with_english_translation_dict)

    print("Downloading mp3s...")
    for item in ultimate_dict.items():

        word = item[0]

        try:
            mp3url = item[1]['mp3_URL']
        except KeyError:
            unsuccessful_words_list.append(item[0])
            continue

        if mp3url:
            mp3 = download_mp3(word, mp3url, download_directory)
            file_paths.append(mp3)
        else:
            continue

    print("Normalising volume for each mp3...")
    for file in file_paths:
        normalize_audio(file)

    create_combined_mp3 = input("\tWould you like to also create an mp3 combining all of the mp3s downloaded? (Y/N):")

    if create_combined_mp3 in ("Y", "y", "YES", "yes"):
        print("Creating combined mp3...")
        merge_mp3s(file_paths, download_directory, folder_name)
    else:
        print("Skipping creation of combined mp3...")

    print("Writing log files...")

    end_time = time.time()
    time_taken = round(end_time - start_time, 2)

    total_words_count = len(original_word_list)
    unsuccessful_words_count = len(unsuccessful_words_list)
    successful_words_count = total_words_count - unsuccessful_words_count

    processing_time_msg = "Processing time: " + str(time_taken)
    processed_words_msg = "Processed words: " + str(total_words_count)
    successful_words_msg = "Successfully downloaded words: " + str(successful_words_count)
    download_directory_msg = "Download directory : " + download_directory

    log_msg = "%s\n%s\n%s\n%s" % (
    processing_time_msg, processed_words_msg, successful_words_msg, download_directory_msg)

    create_log_files(ultimate_dict, log_file_name, log_msg)

    print("\n" + log_msg)

main()
