# Videoconverter

## What's inside
Ubuntu based container with an ffmpeg installation


## Usage
```docker run -it -v "<absolute host path>":"/videos" -w "/videos" videoconverter ffmpeg -i "<relative path to source video>" -s hd720 "<outputfile>"```


### Size -s
Specifies video output size.

https://ffmpeg.org/ffmpeg-all.html#Video-size