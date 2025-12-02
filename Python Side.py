import time
import serial
import pyaudio
import wave
import whisper
import os


from transformers import pipeline, logging
logging.set_verbosity_error()


# serial

PORT = "COM5"
BAUD_RATE = 9600
OUTPUT_DIR = "audio_files/"


if not os.path.exists(OUTPUT_DIR):
   os.makedirs(OUTPUT_DIR)


try:
   ser = serial.Serial(PORT, BAUD_RATE, timeout=1)
   time.sleep(2)

   ser.flushInput()

   print(f"Connected to Arduino on {PORT}. Waiting for START signal...")
except serial.SerialException as e:
   print(f"ERROR opening {PORT}. Check wiring + port name.")
   print(e)
   exit()


FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
audio = pyaudio.PyAudio()
stream = None
frames = []
is_recording = False
current_filename = ""


# Sumarization


summarizer = pipeline(
   "summarization",
   model="t5-base",
   tokenizer="t5-base"
)




# Record


def start_recording():
   global stream, frames, is_recording, current_filename


   current_filename = f"{OUTPUT_DIR}lecture_{int(time.time())}.wav"
   print("\nRecording started...")


   stream = audio.open(
       format=FORMAT,
       channels=CHANNELS,
       rate=RATE,
       input=True,
       frames_per_buffer=CHUNK
   )


   frames = []
   is_recording = True




def stop_recording(filename):
   global stream, is_recording
   is_recording = False


   print("Recording stopped. Saving file...")


   stream.stop_stream()
   stream.close()


   with wave.open(filename, 'wb') as wf:
       wf.setnchannels(CHANNELS)
       wf.setsampwidth(audio.get_sample_size(FORMAT))
       wf.setframerate(RATE)
       wf.writeframes(b''.join(frames))


   print(f"Saved audio: {filename}")
   transcribe_audio(filename)




# Transcribe


def transcribe_audio(filename):
   print("Running Whisper transcription...")


   model = whisper.load_model("base")
   result = model.transcribe(filename)


   text = result["text"]


   # save transcript
   txt_filename = filename.replace(".wav", ".txt")
   with open(txt_filename, "w", encoding="utf-8") as f:
       f.write(text)


   print(f"Transcription saved as: {txt_filename}")


   print("Running summarization...")
   run_summarization(text, filename)




def run_summarization(text, filename):


   # Summarize
   summary = summarizer(
       "Summarize the following lecture accurately: " + text,
       max_length=100,
       min_length=30,
       num_beams=5
   )[0]["summary_text"]


   # save summary
   summary_filename = filename.replace(".wav", "_summary.txt")
   with open(summary_filename, "w", encoding="utf-8") as f:
       f.write(summary)


   print(f"Summary saved as: {summary_filename}")
   print("SUMMARY COMPLETE.")


try:
   while True:


       if ser.in_waiting > 0:
           line = ser.readline().decode().strip()


           if line == "START":
               start_recording()


           elif line == "STOP":
               stop_recording(current_filename)


       if is_recording and stream:
           try:
               frames.append(stream.read(CHUNK, exception_on_overflow=False))
           except IOError as e:
               if e.errno == -9988:
                   print("Audio buffer overflow.")
               else:
                   raise e


except KeyboardInterrupt:
   print("\nExiting program.")


finally:
   if ser.is_open:
       ser.close()
   if stream:
       stream.stop_stream()
       stream.close()
   audio.terminate()
   print("Cleanup complete.")
