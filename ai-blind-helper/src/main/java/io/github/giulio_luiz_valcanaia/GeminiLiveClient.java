package io.github.giulio_luiz_valcanaia;

import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;

import javax.sound.sampled.LineUnavailableException;
import java.io.IOException;
import java.net.URI;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;

/**
 * Responsibility: Manage the WebSocket connection lifecycle and coordinate
 * interactions between the audio hardware and the Gemini protocol.
 */
public class GeminiLiveClient extends WebSocketClient {

    private final AudioHardwareManager audioManager;
    private final GeminiProtocolEncoder encoder;
    private final GeminiResponseProcessor processor;

    // Executor for handling microphone audio sending loop
    private final ScheduledExecutorService microphoneExecutor = Executors.newSingleThreadScheduledExecutor();

    private volatile boolean isRunning = true;
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

        // Start audio capture and microphone sending thread
        audioManager.startCapture();

        Executors.newSingleThreadExecutor().execute(this::microphoneSendLoopWithSleep);
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
        isRunning = false;
        microphoneExecutor.shutdownNow();

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
}
