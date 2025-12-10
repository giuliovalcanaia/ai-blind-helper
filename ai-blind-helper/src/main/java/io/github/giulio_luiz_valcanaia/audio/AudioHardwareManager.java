package io.github.giulio_luiz_valcanaia.audio;

import javax.sound.sampled.*;
import java.io.Closeable;
import java.io.IOException;

public class AudioHardwareManager implements Closeable {

    // Input format (microphone). Gemini supports high sample rates.
    private static final AudioFormat INPUT_FORMAT = new AudioFormat(16000, 16, 1, true, false);

    // Output format (speaker)
    private static final AudioFormat OUTPUT_FORMAT = new AudioFormat(24000, 16, 1, true, false);

    private TargetDataLine microphone;
    private SourceDataLine speaker;

    public AudioHardwareManager() throws LineUnavailableException {
        configureAudioHardware();
    }

    /**
     * Initializes and configures speaker and microphone hardware.
     */
    private void configureAudioHardware() throws LineUnavailableException {
        System.out.println("[DEBUG: AudioHardwareManager] Starting audio hardware configuration");

        // --- 1. Configure Speaker ---
        try {
            DataLine.Info speakerInfo = new DataLine.Info(SourceDataLine.class, OUTPUT_FORMAT);
            speaker = (SourceDataLine) AudioSystem.getLine(speakerInfo);
            speaker.open(OUTPUT_FORMAT);
            System.out.println("[DEBUG: AudioHardwareManager] Speaker line opened. Buffer size: " + speaker.getBufferSize());
            System.out.println("[DEBUG: AudioHardwareManager] Output format: " + speaker.getFormat());
            speaker.start();
            System.out.println("[DEBUG: AudioHardwareManager] Speaker started.");
            System.out.println("[DEBUG: AudioHardwareManager] Speaker Line Info: " + speaker.getLineInfo());
        } catch (Exception e) {
            System.err.println("[WARNING] Speaker initialization failed: " + e.getMessage());
        }

        // --- 2. Configure Microphone ---
        DataLine.Info micInfo = new DataLine.Info(TargetDataLine.class, INPUT_FORMAT);

        // Attempt 1: Standard Java “system default”
        try {
            System.out.println("[DEBUG: AudioHardwareManager] Trying system default microphone...");
            microphone = (TargetDataLine) AudioSystem.getLine(micInfo);
            microphone.open(INPUT_FORMAT);
            System.out.println("[DEBUG: AudioHardwareManager] SUCCESS! System default microphone opened.");
            return;
        } catch (Exception e) {
            System.out.println("[DEBUG] Failed to open default microphone: " + e.getMessage());
            System.out.println("[DEBUG] Attempting manual mixer search...");
        }

        // Attempt 2: Iterate through mixers manually
        Mixer.Info[] mixers = AudioSystem.getMixerInfo();
        for (Mixer.Info info : mixers) {
            String name = info.getName().toLowerCase();

            if (name.contains("playback") || name.contains("output")) continue;

            if (name.contains("default") || name.contains("pulse") || name.contains("pipewire") || name.contains("java")) {
                Mixer mixer = AudioSystem.getMixer(info);

                if (mixer.isLineSupported(micInfo)) {
                    try {
                        System.out.println("[DEBUG] Trying mixer: " + info.getName());
                        microphone = (TargetDataLine) mixer.getLine(micInfo);
                        microphone.open(INPUT_FORMAT);
                        System.out.println("[DEBUG: AudioHardwareManager] SUCCESS via mixer: " + info.getName());
                        return;
                    } catch (Exception ignored) {}
                }
            }
        }

        if (microphone == null) {
            throw new LineUnavailableException("[CRITICAL ERROR] Could not access microphone at required sample rate.");
        }
    }

    /**
     * Starts capturing audio from the microphone.
     */
    public void startCapture() {
        if (microphone != null) {
            microphone.start();
            System.out.println("[DEBUG: AudioHardwareManager] Microphone capture STARTED.");
        }
    }

    public void stopCapture() {
        if (microphone != null) {
            microphone.stop();
        }
    }

    /**
     * Reads audio data from the microphone.
     */
    public int readAudio(byte[] buffer) {
        if (microphone != null) {
            return microphone.read(buffer, 0, buffer.length);
        }
        return 0;
    }

    /**
     * Plays PCM audio through the speaker.
     */
    public void playAudio(byte[] audioData) {
        if (speaker == null || !speaker.isOpen()) {
            System.out.println("[WARNING: AudioHardwareManager] Speaker is not ready for playback.");
            return;
        }

        int bytesToWrite = audioData.length;

        // Ensure even number of bytes (16-bit frames)
        if (bytesToWrite % 2 != 0) {
            bytesToWrite--;
            System.out.println("[WARNING: AudioHardwareManager] Odd chunk size detected. Adjusted to " + bytesToWrite + " bytes.");
        }

        if (bytesToWrite > 0) {
            speaker.write(audioData, 0, bytesToWrite);
        }
    }

    @Override
    public void close() throws IOException {
        if (microphone != null) microphone.close();
        if (speaker != null) speaker.close();
    }

    /**
     * Returns the MIME type for microphone input (required by Gemini).
     */
    public String getInputMimeType() {
        return String.format("audio/pcm;rate=%d", (int) INPUT_FORMAT.getSampleRate());
    }
}
