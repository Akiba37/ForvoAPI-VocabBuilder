# ForvoAPI-VocabBuilder

This is a python script made to download mp3s from a list of Japanese words using the ForvoAPI.

It takes a .txt file as an input and attempts to download the mp3 for the words on each line of that file.

The script also requests an output directory for the mp3s to be downloaded to, then produces a summary log 
containing information around how many of the words were found by the API/ downloaded successfully.

To use this script you will need an API key retrievable at https://api.forvo.com/ - unless you subscribe to
one of the more expensive plans, there's a daily limit on how many requests you can make. I've never
exceeded this, so I'm not sure exactly what would happen if you did, but it's probably best to adhere to that quota.

The primary reason for making this was to improve the usefulness of my Anki deck,
allowing me to learn the correct pronunciation for words whilst picking up
new vocabulary.

I'm quite new to python and programming in general, so if you spot anything that
could be written better / any bugs, please let me know or feel free to make
modifications.

Thanks, Ollie.
