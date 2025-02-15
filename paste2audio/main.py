#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import pyperclip
import ffmpeg
import numpy as np
from gtts import gTTS
from PyQt6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel,
    QListWidget, QComboBox, QHBoxLayout, QProgressBar, QSlider
)
from PyQt6.QtCore import (
    QSize, Qt, QTimer
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl, QObject, pyqtSignal, QThread
from PyQt6.QtGui import QMovie, QPixmap
from PyQt6.QtGui import QIcon
# Importing KOKORO
from kokoro import KPipeline
import soundfile as sf


# Mapping of speed factors to text values
mapReproductionSpeeds = {"1x": 1.0, "1.2x": 1.2, "1.5x": 1.5, "1.75x": 1.75}

class ConversionWorker(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
 
    def __init__(self, text):
        super().__init__()
        self.text = text
        self.pipeline = KPipeline(lang_code='b')
        self.generator = self.pipeline(
                self.text, voice='bf_emma', # <= change voice here
                speed=1, split_pattern=r'\n+'
            )
        
    
    
    def run(self):
        try:
            # Clean the text and get first 10 chars for filename
            clean_text = ''.join(c for c in self.text if c.isalnum() or c.isspace())
            recording_name = clean_text[:10].strip().replace(" ", "_")                
            current_audio_file = f"data/temp/{recording_name}.wav"
            # Ensure unique filename
            counter = 1
            while os.path.exists(current_audio_file):
                current_audio_file = f"data/temp/{recording_name}_{counter}.wav"
                counter += 1

            # 4️⃣ Generate, display, and save audio files in a loop.
            audio_segments = []
            for i, (gs, ps, audio) in enumerate(self.generator):
                sf.write(f'data/temp/{i}.wav', audio.numpy(), 24000, 'PCM_16')
                audio_segments.append(f'data/temp/{i}.wav')

            # Read and concatenate all audio segments
            combined_audio = []
            for segment in audio_segments:
                data, samplerate = sf.read(segment)
                combined_audio.append(data)

            # Concatenate all audio data
            combined_audio = np.concatenate(combined_audio)

            # Save the combined audio as wav
            sf.write(current_audio_file, combined_audio, samplerate, 'PCM_16')

            # Delete temporary audio segment files
            for segment in audio_segments:
                try:
                    if os.path.exists(segment):
                        os.remove(segment)
                except Exception as e:
                    print(f"Error deleting temporary file {segment}: {e}")

            self.finished.emit(current_audio_file)
        except Exception as e:
            self.error.emit(str(e))

class SpeedConverter(QObject):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    def __init__(self, text, recording_count, speed_factor=1.0):
        super().__init__()
        self.text = text
        self.recording_count = recording_count
        self.speed_factor = speed_factor
 
    def run(self):
        try:
            base_name = os.path.basename(self.current_audio_file)
            name_without_ext = os.path.splitext(base_name)[0]
            processed_audio_file = f"data/temp/processed_{name_without_ext}.wav"
            
            if self.speed_factor != 1.0:
                input_audio = ffmpeg.input(self.current_audio_file)
                output_audio = ffmpeg.output(input_audio.filter('atempo', self.speed_factor), processed_audio_file)
                ffmpeg.run(output_audio, overwrite_output=True)
            else:
                os.rename(self.current_audio_file, processed_audio_file)
            self.finished.emit(processed_audio_file)
        except Exception as e:
            self.error.emit(str(e))

class AudioPlayerApp(QWidget):
    def __init__(self):
        super().__init__()
        os.makedirs("data/temp", exist_ok=True)
        
        self.setWindowTitle("paste2audio")
        self.setGeometry(100, 100, 400, 300)
        
        app_icon = QIcon("data/assets/VOX.icns")
        QApplication.setWindowIcon(app_icon)
        
        layout = QVBoxLayout()
        
        # Progress Bar and Time Display
        self.progress_bar = QProgressBar()
        self.current_time_label = QLabel("0:00")
        self.total_time_label = QLabel("0:00")
        
        time_layout = QHBoxLayout()
        time_layout.addWidget(self.current_time_label)
        time_layout.addWidget(self.progress_bar)
        time_layout.addWidget(self.total_time_label)
        layout.addLayout(time_layout)
        
        # Playback Controls
        controls_layout = QHBoxLayout()
        self.play_pause_btn = QPushButton("Play")
        self.play_pause_btn.setEnabled(False)
        self.speed_label = QLabel("Speed:")
        self.speed_selector = QComboBox()
        self.speed_selector.addItems(list(mapReproductionSpeeds.keys()))
        
        controls_layout.addWidget(self.play_pause_btn)
        controls_layout.addWidget(self.speed_label)
        controls_layout.addWidget(self.speed_selector)
        layout.addLayout(controls_layout)
        
        # Volume Control
        self.volume_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        volume_layout.addWidget(self.volume_slider)
        layout.addLayout(volume_layout)
        
        # File List and Delete Button
        self.file_list = QListWidget()
        layout.addWidget(self.file_list)
        
        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setEnabled(False)
        self.delete_btn.clicked.connect(self.delete_selected_audio)
        layout.addWidget(self.delete_btn)
        
        # Paste & Convert Button
        self.paste_btn = QPushButton("Paste & Convert")
        self.paste_btn.clicked.connect(self.start_conversion_thread)
        layout.addWidget(self.paste_btn)

        # Add Reset Button
        self.reset_btn = QPushButton("Reset")
        controls_layout.addWidget(self.reset_btn)
        self.reset_btn.clicked.connect(self.reset_playback)
        self.reset_btn.setEnabled(False)  # Enable when a file is selected

        # Status Section
        self.status_label = QLabel("Waiting for input...")
        layout.addWidget(self.status_label)
        self.status_icon = QLabel()
        self.spinner_movie = QMovie("data/assets/spinner.gif")
        self.spinner_movie.setScaledSize(QSize(50, 50))
        self.checkmark_icon = QPixmap("data/assets/checkmark.png").scaled(50, 50) 
        layout.addWidget(self.status_icon)
        
        self.setLayout(layout)
        
        # Audio Player Setup
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(self.volume_slider.value() / 100.0)
        self.volume_slider.valueChanged.connect(lambda v: self.audio_output.setVolume(v / 100.0))
        
        # Update progress bar and time
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress_bar)
        
        # Connect signals
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.positionChanged.connect(self.on_position_changed)
        self.play_pause_btn.clicked.connect(self.play_pause_audio)
        self.speed_selector.currentTextChanged.connect(self.update_speed)
        self.file_list.itemSelectionChanged.connect(self.on_selection_changed)
        
        self.current_audio_file = None
        self.processed_audio_file = None
        
        # Conversion thread setup
        self.conversion_thread = QThread()
        self.conversion_worker = None

    def update_progress_bar(self):
        if self.player.duration() > 0:
            progress = (self.player.position() / self.player.duration()) * 100
            self.progress_bar.setValue(int(progress))
            self.current_time_label.setText(self.format_time(self.player.position()))
    
    def format_time(self, milliseconds):
        seconds = int((milliseconds // 1000) % 60)
        minutes = int((milliseconds // (1000 * 60)) % 60)
        return f"{minutes}:{seconds:02d}"

    def on_duration_changed(self, duration):
        self.total_time_label.setText(self.format_time(duration))
    
    def on_position_changed(self, position):
        if self.player.duration() > 0:
            progress = (position / self.player.duration()) * 100
            self.progress_bar.setValue(int(progress))
            self.current_time_label.setText(self.format_time(position))
    
    def update_speed(self):
        speed_factor = mapReproductionSpeeds[self.speed_selector.currentText()]
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.setPlaybackRate(speed_factor)
        
    def on_selection_changed(self):
        selected = bool(self.file_list.selectedItems())
        self.delete_btn.setEnabled(selected)
        self.play_pause_btn.setEnabled(selected)
        self.reset_btn.setEnabled(selected)
    
    def delete_selected_audio(self):
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return
        selected_item = selected_items[0]
        file_path = selected_item.text()
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
        self.file_list.takeItem(self.file_list.row(selected_item))
    
    def start_conversion_thread(self):
        """Handles Paste from Clipboard and converts to speech."""
        text = pyperclip.paste().strip()

        if not text:
            self.status_label.setText("Clipboard is empty!")
            return
        
        # Disable the button to prevent multiple clicks while processing
        self.paste_btn.setEnabled(False)
        self.status_label.setText("Converting to speech...")
        self.status_icon.setMovie(self.spinner_movie)
        self.spinner_movie.start()
        
        # Create new worker and move it to the thread
        # self.conversion_worker = ConversionWorker(text, self.recording_count)
        self.conversion_worker = ConversionWorker(text)
        self.conversion_worker.moveToThread(self.conversion_thread)
        
        # Connect signals
        self.conversion_worker.finished.connect(self.on_conversion_finished)
        self.conversion_worker.error.connect(self.on_conversion_error)
        self.conversion_thread.started.connect(self.conversion_worker.run)
        
        # Start the thread
        if not self.conversion_thread.isRunning():
            self.conversion_thread.start()
        else:
            # If the thread is already running, stop it and start again
            self.conversion_thread.terminate()
            self.conversion_thread.wait()
            self.conversion_thread.start()
    
    def on_conversion_finished(self, processed_audio_file):
        """Handle completion of conversion."""
        self.spinner_movie.stop()
        self.status_icon.setPixmap(self.checkmark_icon)
        
        # Add the new file to list and select it
        self.file_list.addItem(processed_audio_file)
        # Get the last item (newest file) and select it
        last_item = self.file_list.item(self.file_list.count() - 1)
        self.file_list.setCurrentItem(last_item)
        
        # Update the current audio files
        self.current_audio_file = processed_audio_file
        self.processed_audio_file = processed_audio_file
        
        # Enable buttons
        self.play_pause_btn.setEnabled(True)
        self.play_pause_btn.setText("Play")
        self.paste_btn.setEnabled(True)
        self.status_label.setText("Conversion complete! Ready to play.")
    
    def on_conversion_error(self, error_message):
        """Handle errors during conversion."""
        self.spinner_movie.stop()
        self.status_icon.clear()  
        self.status_label.setText(f"Error: {error_message}")
        self.paste_btn.setEnabled(True)
        print(f"Conversion Error: {error_message}")


    def play_pause_audio(self):
        """Plays or pauses the generated audio with the selected speed."""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return
        
        current_selected_file = selected_items[0].text()

        print("== File ====")
        print(current_selected_file)
        print(self.current_audio_file)
        print(" === END ====")
 
        if (current_selected_file != self.current_audio_file) or (self.player.playbackState() == QMediaPlayer.PlaybackState.StoppedState) :
            # Load new file and start playing
            self.player.setSource(QUrl.fromLocalFile(current_selected_file))
            self.current_audio_file = current_selected_file
            
            # Ensure playback is stopped before starting a new track
            if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.player.pause()
            
            self.player.play()
            self.play_pause_btn.setText("Pause")
            self.timer.start(100)
        else:
            # Toggle play/pause without reloading the file
            if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.player.pause()
                self.play_pause_btn.setText("Play")
                self.timer.stop()
            else:
                # Load new file and start playing
                self.player.play()
                self.play_pause_btn.setText("Pause")
                self.timer.start(100)

    def reset_playback(self):
        if not self.file_list.selectedItems():
            return
        
        current_selected_file = self.file_list.selectedItems()[0].text()
        
        # Check if the selected file is different from currently loaded
        if current_selected_file != self.current_audio_file:
            self.player.setSource(QUrl.fromLocalFile(current_selected_file))
            self.current_audio_file = current_selected_file
            
            # Stop any ongoing playback when changing files
            if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                self.player.pause()
        
        # Reset position to beginning
        self.player.setPosition(0)
        self.progress_bar.setValue(0)
        self.current_time_label.setText("0:00")
        
        # Ensure playback is stopped and UI reflects reset state
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        
        self.play_pause_btn.setText("Play")
        self.timer.stop() 

    def closeEvent(self, event):
        temp_folder = "data/temp"
        if os.path.exists(temp_folder):
            for file_name in os.listdir(temp_folder):
                file_path = os.path.join(temp_folder, file_name)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
        super().closeEvent(event)

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Paste2Audio")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("YourOrganizationName")
    app.setOrganizationDomain("yourdomain.com")
    window = AudioPlayerApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()