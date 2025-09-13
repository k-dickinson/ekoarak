# How this shit works

First thing that you do is put your song that is in mp3 format into the separate.py script. What will happen is that it will be split into 2 new mp3s. the first one is an instrumental track while the second is the vocals track. for our case we will be using "A Thousand Years" by Christina Perri. We then take out vocals track and put that into the lyrics2notes.py script. This takes the vocal audio file, extracts the main melody, and then analyzes the audio and tries to find the main notes that a person would sing (the melody line). It then groups and merges notes so the melody flows better and isn’t choppy. It saves the melody as a MIDI file (for playback or editing), a JSON file (with note data), and a MusicXML file (which we will use for sheet music).

For my gooners, what you need to know is that you first do the separate.py with the full song, then run the lyrics2notes.py script and select the vocals track. then you will get a .musicXML file.

The sheet music doesn't sound perfect but I think that we can work with it (we dont really have an option).
