package io.github.giulio_luiz_valcanaia.client;

import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;

import io.github.giulio_luiz_valcanaia.audio.AudioHardwareManager;
import io.github.giulio_luiz_valcanaia.protocol.GeminiProtocolEncoder;
import io.github.giulio_luiz_valcanaia.protocol.GeminiResponseProcessor;

import javax.sound.sampled.LineUnavailableException;
import java.io.IOException;
import java.net.URI;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;

/**
 * Responsibility: Manage the WebSocket connection lifecycle and coordinate
 * interactions between the audio hardware and the Gemini protocol.
 */
public class GeminiLiveClient extends WebSocketClient {

    private final AudioHardwareManager audioManager;
    private final GeminiProtocolEncoder encoder;
    private final GeminiResponseProcessor processor;

    private Thread audioThread = null;

    private volatile boolean isRunning = true; // Flag that is just used on the loop for mic reading
    private static final int BUFFER_SIZE = 1024; // Increased for driver compatibility

    public GeminiLiveClient(URI serverUri) throws LineUnavailableException {
        super(serverUri);
        System.out.println("[DEBUG: GeminiLiveClient] Client created. Server URI: " + serverUri);

        this.audioManager = new AudioHardwareManager();
        this.encoder = new GeminiProtocolEncoder();
        this.processor = new GeminiResponseProcessor(audioManager);
    }

    // --- WebSocket Events ---

    @Override
    public void onOpen(ServerHandshake handshakedata) {
        System.out.println("[DEBUG: GeminiLiveClient] CONNECTION ESTABLISHED. Connected to Gemini Live API.");
        System.out.println("[DEBUG: GeminiLiveClient] Calling encoder setup function...");

        // Send initial SETUP message
        String setupMessage = encoder.createSetupMessage();
        System.out.println("[DEBUG: GeminiLiveClient] Sending initial SETUP message:");
        System.out.println("[DEBUG: GeminiLiveClient] SetupMessage: " + setupMessage);
        send(setupMessage);
    }

    /**
     * Callback for UTF-8 text messages received from the remote host.
     */
    @Override
    public void onMessage(String message) {
        System.out.println("[DEBUG: GeminiLiveClient] onMessage() called for text message.");
        System.out.println("[DEBUG: GeminiLiveClient] Received (String): " + message);
        processor.processMessage(message);
    }

    /**
     * Callback for binary messages.
     */
    @Override
    public void onMessage(ByteBuffer bytes) {
        System.out.println("[DEBUG: GeminiLiveClient] Buffer initial position: " + bytes.position());

        int size = bytes.remaining();
        System.out.println("[DEBUG: GeminiLiveClient] ByteBuffer remaining size: " + size + " bytes");

        byte[] audioChunk = new byte[size];
        bytes.get(audioChunk);

        String jsonString = new String(audioChunk, StandardCharsets.UTF_8);

        System.out.println("[DEBUG] Generated JSON string: " + jsonString);

        processor.processMessage(jsonString);
    }

    @Override
    public void onClose(int code, String reason, boolean remote) {
        System.out.println("\n[DEBUG: GeminiLiveClient] CONNECTION CLOSED. Code: " + code + ", Reason: " + reason);
        
        try {
            audioManager.close();
        } catch (IOException e) {
            System.err.println("[ERROR: GeminiLiveClient] Failed to close audio resources: " + e.getMessage());
        }
    }

    @Override
    public void onError(Exception ex) {
        System.err.println("\n[ERROR: GeminiLiveClient] WebSocket fatal error: " + ex.getMessage());
        ex.printStackTrace();
    }

    /**
     * Microphone audio loop using Thread.sleep when no audio is available.
     * Prevents high CPU usage and allows the audio driver time to refill buffers.
     */
    private void microphoneSendLoopWithSleep() {
        System.out.println("[DEBUG: GeminiLiveClient] Microphone send loop started (manual thread).");
        final byte[] buffer = new byte[BUFFER_SIZE];
        final String mimeType = audioManager.getInputMimeType();
        System.out.println("[DEBUG: GeminiLiveClient] MimeType: " + mimeType);

        while (isRunning && isOpen()) {
            int bytesRead = audioManager.readAudio(buffer);

            if (bytesRead > 0) {
                try {
                    String audioMessage = encoder.createAudioInputMessage(buffer, mimeType);
                    send(audioMessage);
                } catch (Exception e) {
                    System.err.println("[ERROR: GeminiLiveClient] Error sending audio chunk: " + e.getMessage());
                }
            } else {
                try {
                    Thread.sleep(200); // Allow buffer fill time
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    System.err.println("[ERROR: GeminiLiveClient] Audio thread interrupted.");
                    break;
                }
            }
        }

        System.out.println("[DEBUG: GeminiLiveClient] Stopping audio send thread.");
    }

    /**
     * Gracefully stops the client.
     */
    public void stopClient() {
        this.isRunning = false;

        if (this.isOpen()) {
            System.out.println("[DEBUG: GeminiLiveClient] Stopping client and closing WebSocket.");
            this.close();
        }
    }

    public void startAudioCapture() {
        // Previne a criação de múltiplas threads se já estiver rodando
        if (isRunning || (audioThread != null && audioThread.isAlive())) {
            System.out.println("[WARN: GeminiLiveClient] Audio capture already running.");
            return;
        }

        // 1. Inicia a captura de hardware (recurso caro)
        audioManager.startCapture();
        
        // 2. Define a flag e inicia a thread do loop
        isRunning = true;
        audioThread = new Thread(this::microphoneSendLoopWithSleep, "MicrophoneSendThread");
        audioThread.start();
        System.out.println("[DEBUG: GeminiLiveClient] Audio capture started.");
    }

    public void stopAudioCapture() {
        if (!isRunning) {
            return;
        }
        
        System.out.println("[DEBUG: GeminiLiveClient] Attempting to stop audio capture and thread.");

        // 1. Define a flag para sair do loop 'while'
        isRunning = false;
        
        // 2. Para a captura de hardware (libera recurso caro)
        audioManager.stopCapture(); 

        // 3. Interrompe a thread caso ela esteja em Thread.sleep(200)
        if (audioThread != null && audioThread.isAlive()) {
            audioThread.interrupt();
        }
        
        // Limpa a referência da thread
        audioThread = null;
        
        System.out.println("[DEBUG: GeminiLiveClient] Audio capture stopped.");
    }
    
}
