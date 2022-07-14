import random
import re
import lyricsgenius
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
from dotenv import load_dotenv
import os
from unidecode import unidecode
import tweepy
from time import sleep

# add desired artist name and water_mark
# DO NOT FORGET TO ADD ARTIST'S SONGS TO song_list.txt file!!
# Please replace everything as mentioned
artist_name = "<artist name>"
your_water_mark = "<your watermark> BOT"

# to load tokens from .env file
# in the .env file add all your tokens
load_dotenv()

# Twitter API tokens
CONSUMER_KEY = os.getenv('CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')
ACCESS_KEY = os.getenv('ACCESS_KEY')
ACCESS_SECRET = os.getenv('ACCESS_SECRET')

# Genius Lyrics Tokens
genius_client_access_token = os.getenv('genius_client_access_token')


def choose_song():
    # in song_list.txt add desired songs
    with open("song_list.txt", "r", encoding="utf-8", ) as f:
        lines = f.readlines()
        # choose a random song from song_list.txt
        rand_line = random.randint(0, len(lines) - 1)
        song_name = lines[rand_line].replace("\n", "")

    # authenticate to genius API
    genius = lyricsgenius.Genius(genius_client_access_token)

    # get the lyrics of the song
    while True:
        try:
            random_song = song_name
            lyrics = genius.search_song(song_name, artist_name).lyrics
            break
        except Exception as e:
            print(e)
            sleep(5)
            continue

    return lyrics, random_song, song_name


def clean_lyrics(lyrics):
    lines = lyrics.split('\n')

    for i in range(len(lines)):
        if lines[i] == "" or "[" in lines[i]:
            lines[i] = "?"

    lines = [j for j in lines if j != "?"]

    # removes unwanted text
    remove_url = 'Embed'

    indx = lines[-1].find(remove_url)

    for i in range(len(lines[-1])):

        if not lines[-1][indx - 1].isalpha():
            lines[-1] = lines[-1][0:indx - 1]
            indx = indx - 1
        else:
            break

    # remove special characters
    for k in range(len(lines)):
        lines[k] = unidecode(lines[k])

    while True:
        # create a list of random numbers
        num_list = list(range(1, len(lines) - 1))
        random.shuffle(num_list)
        random_num = num_list.pop()

        # choose lyrics based on the random number generated
        line_1 = lines[random_num]
        line_2 = lines[random_num + 1]

        # constraints to drop long lyrics so text fits in an image
        if len(line_1) > 58 or len(line_2) > 58:
            continue
        else:
            break

    line_1 = line_1.replace("\\", "")
    line_2 = line_2.replace("\\", "")

    return line_1, line_2


def get_text_dimensions(text_string, font):
    ascent, descent = font.getmetrics()

    text_width = font.getmask(text_string).getbbox()[2]
    text_height = font.getmask(text_string).getbbox()[3] + descent

    return text_width, text_height


# this function helps in positioning the lyrics on an image
def add_new_line(font_poem, start_height):
    lyrics, random_poem, song_name = choose_song()
    line_1, line_2 = clean_lyrics(lyrics)

    line_1_width, line_1_height = get_text_dimensions(line_1, font_poem)
    line_2_width, line_2_height = get_text_dimensions(line_2, font_poem)
    random_poem_width, random_poem_height = get_text_dimensions(line_2, font_poem)

    y = start_height
    y_2 = y + 70

    if line_1_width + 70 > 450:

        width = len(line_1) * 20
        counter = 0

        while width > 450:
            width = width // 2

            if width - 450 > 30:
                counter = 0
            else:
                counter = 1

            counter = counter + 1

        words = (line_1.split())
        index = (len(words) // 2) + 1

        if counter > 2:
            pos = len(words) // counter
            add = 0

            for i in range(len(words)):
                if i % pos == 0 and i != 0:
                    words.insert(i + add, '\n')
                    add = add + 1

            line_1 = ' '.join(x for x in words).replace('\n ', '\n')
            line_1_width, line_1_height = get_text_dimensions(line_1, font_poem)

            y = y - 100
            y_2 = y + line_1_height + counter * line_1_height

        else:
            line_1 = " ".join(words[:index // 2 + 1]) + "\n" + " ".join(words[index // 2 + 1:])
            y_2 = y + line_1_height + 50

    y_3 = y_2 + 50

    if line_2_width + 50 >= 400:
        words = (line_2.split())
        index = (len(words) // 2) + 1
        line_2 = " ".join(words[:index // 2 + 1]) + "\n" + " ".join(words[index // 2 + 1:])

        y_3 = y_2 + line_2_height + 50

    return line_1, line_2, random_poem, y_2, y_3, random_poem_width, line_2_width, song_name


# this function adds the lyrics on image using PIL
def draw_poem():
    # provided templates. Adding new templates must be larger than 560x510
    templates = ['beige.jpg', 'silver.jpg', 'silver2.jpg',
                 'silver3.jpg', 'lightPink.jpg', 'white.png', 'purple.jpg', 'texture.jpg']
    # choose a random template
    rand_indx = random.randrange(0, 6)
    poem_img = Image.open(fr'templates/{templates[rand_indx]}')
    # crop image for twitter
    poem_img = poem_img.crop((0, 0, 560, 510))

    draw = ImageDraw.Draw(poem_img)

    font_size = 35
    font_poem = ImageFont.truetype('fonts/MinionPro-Regular.otf', font_size)
    poem_name = ImageFont.truetype('fonts/MinionPro-It.otf', 20)
    water_mark = ImageFont.truetype('fonts/MinionPro-Medium.otf', 15)

    image_height, image_width = poem_img.size
    start_height = image_height // 2 - 100

    line_1, line_2, random_poem, y_2, y_3, \
    random_poem_width, line_2_width, song_name = add_new_line(font_poem, start_height)

    start = 70
    x_name = line_2_width // 2 - 20

    if random_poem_width + 270 >= 370 or len(line_2) > 50:
        random_poem = '-' + f'"{random_poem}"' + "\n" + " by " + artist_name

        # if constraint is met, move lyrics to the right
        if len(line_2) > 47:
            x_name = line_2_width // 2 - 200

        # if song name is long make an abbreviation
        if len(song_name) > 32:
            abrv = ''.join(re.findall(r"\b(\w)", song_name.upper()))
            random_poem = '-' + f'"{abrv}"' + "\n" + " by " + artist_name

    else:
        random_poem = '-' + f'"{random_poem}"' + " by " + artist_name

    # can be tuned
    max_font_size = 45

    # decrease font size if text is getting cropped
    if len(line_1) > max_font_size or len(line_2) > max_font_size:
        font_poem = ImageFont.truetype('fonts/MinionPro-Regular.otf', font_size - 8)

    draw.multiline_text((start, start_height), line_1, fill=(0, 0, 0), font=font_poem, spacing=10)
    draw.multiline_text((start, y_2), line_2, fill=(0, 0, 0), font=font_poem, spacing=10)
    draw.multiline_text((x_name, y_3), random_poem, fill=(0, 0, 0), font=poem_name, spacing=10)
    draw.multiline_text((10, start_height - 90), f'-Created By {your_water_mark}', fill=(0, 0, 0), font=water_mark,
                        spacing=10)

    # keeps text only and removes unneeded space
    poem_img = poem_img.crop((0, start_height - 100, 560, y_3 + 100))

    # poem_img.show()
    draw = iobytes(poem_img)
    return draw, random_poem, song_name


# used to save picture in memory before tweeting
def iobytes(my_image):
    img = BytesIO()
    img.name = 'image.jpeg'
    my_image.save(img, 'JPEG', quality=100)
    img.seek(0)
    return img


# authenticate to twitter standard V1.1 API
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
api = tweepy.API(auth)

# used to alternate between plain text tweet and image tweet
rand_tweet = random.randrange(0, 2)

# tweet either text or image based on rand_tweet
while True:
    # tweets every ~=3 hours (10900 seconds)
    delay_in_seconds = 10900

    if rand_tweet == 0:
        img, random_poem, song_name = draw_poem()

        # tweets an image
        status = api.update_status_with_media(
            filename="dummy_string", file=img, status=f"{song_name} by #{artist_name.replace(' ', '')}"
        )

    else:
        lyrics, random_song, song = choose_song()
        line1, line2 = clean_lyrics(lyrics)
        tweet = line1 + '\n' + line2 + '\n' + '\n' + "-" + song + f" by {artist_name}"

        # tweets plain text
        status = api.update_status(tweet)

    # sleeps for 3 hours
    sleep(delay_in_seconds)
