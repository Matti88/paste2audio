# Paste2Audio

Paste2Audio is a GUI application that allows you to quickly convert text from your clipboard into natural-sounding speech using the Kokoro model. This app is perfect for listening to your notes, emails, and messages on the go.

## Features

- **Clipboard Integration**: Paste text directly from your clipboard.
- **Natural Voice Conversion**: Leverages Kokoro's new model for high-quality, natural-sounding speech.
- **Playback Controls**: Play, pause, and reset audio playback.
- **Speed Adjustment**: Adjust the playback speed (1x, 1.2x, 1.5x, 1.75x).
- **Volume Control**: Easily adjust the volume.
- **File Management**: View and delete generated audio files.
- **Status Indicators**: Visual feedback during conversion and playback.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/paste2audio.git
    cd paste2audio
    ```

2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Ensure you have the necessary assets in the `data/assets` directory:
    - `VOX.icns`: Application icon
    - `spinner.gif`: Loading spinner
    - `checkmark.png`: Checkmark icon

## Usage

1. Run the application:
    ```sh
    python paste2audio/main.py
    ```

2. The GUI will open. You can now paste text from your clipboard and convert it to speech.

## How to Use

1. **Paste & Convert**: Click the "Paste & Convert" button to paste text from your clipboard and start the conversion process.
2. **Playback Controls**: Use the "Play" button to start playback, "Pause" to pause, and "Reset" to reset the playback to the beginning.
3. **Speed Adjustment**: Select the desired playback speed from the dropdown menu.
4. **Volume Control**: Adjust the volume using the slider.
5. **File Management**: View the list of generated audio files. Select a file to play or delete it using the "Delete Selected" button.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Kokoro](https://kokoro.ai) for their amazing text-to-speech model.
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/intro) for the GUI framework.
- [FFmpeg](https://ffmpeg.org) for audio processing.

Enjoy using Paste2Audio!
