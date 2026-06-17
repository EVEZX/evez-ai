#!/bin/bash
# Vocal strip processor — words intelligible, echoes and harmonies are the trip
cd /home/openclaw/.openclaw/media/inbound/separated/htdemucs/file_70---2f390a97-a7e2-41a7-8886-051c5c99c2b6/

ffmpeg -y -i vocals.wav -filter_complex \
  "[0:a]aecho=0.8:0.88:60:0.4,apad=pad_dur=1[echoed]; \
   [0:a]asetrate=44100*1.5,aresample=44100,atrim=0:215,volume=0.3[high]; \
   [0:a]asetrate=44100*0.7,aresample=44100,atrim=0:215,volume=0.2[low]; \
   [echoed][high][low]amix=inputs=3:duration=longest:dropout_transition=3,volume=1.5,compand=.3|.3:1|1:-90/-60|-60/-40|-40/-30|-20/-20:6:0:-90:0.2" \
  -ar 44100 -ac 1 \
  /home/openclaw/.openclaw/workspace/output_vocal_strip.mp3
