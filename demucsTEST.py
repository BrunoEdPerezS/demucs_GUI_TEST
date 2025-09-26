import demucs.separate
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, "OUTPUT")

demucs.separate.main([
    "--float32", "--clip-mode=rescale",
    "--two-stems", "guitar",
    "-n", "htdemucs_6s",
    "Track.wav",
    "-o", output_dir
])
