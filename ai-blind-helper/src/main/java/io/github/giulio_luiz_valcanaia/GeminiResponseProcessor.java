package io.github.giulio_luiz_valcanaia;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.Base64;

/**
 * Responsibility: Decode and analyze JSON messages received
 * from the Gemini Live API and extract audio for playback.
 * Isolates JSON parsing logic from WebSocket communication.
 */
public class GeminiResponseProcessor {
    private AudioHardwareManager audioManager;

    /**
     * Constructor.
     * @param audioManager The handler responsible for managing audio playback.
     */
    public GeminiResponseProcessor(AudioHardwareManager audioManager) {
        this.audioManager = audioManager;
        System.out.println("[DEBUG: GeminiResponseProcessor] Initialized. Ready to receive messages.");
    }

    /**
     * Processes the full JSON message received from the server.
     * @param message The JSON string received.
     */
    public void processMessage(String message) {
        System.out.println("\n[DEBUG: GeminiResponseProcessor] Message received. Size: " + message.length());

        try {
            JSONObject json = new JSONObject(message);

            if (json.has("serverContent")) {
                JSONObject serverContent = json.getJSONObject("serverContent");

                // 1. Process audio and text (modelTurn)
                if (serverContent.has("modelTurn")) {
                    JSONObject modelTurn = serverContent.getJSONObject("modelTurn");
                    System.out.println("[DEBUG: GeminiResponseProcessor] Found 'modelTurn'. Processing response parts.");
                    JSONArray parts = modelTurn.getJSONArray("parts");

                    for (int i = 0; i < parts.length(); i++) {
                        JSONObject part = parts.getJSONObject(i);

                        // Check for audio (inlineData)
                        if (part.has("inlineData")) {
                            processAudioPart(part);
                        }

                        // Check for partial text output (optional)
                        if (part.has("text")) {
                            System.out.println("[DEBUG: GeminiResponseProcessor] Partial text received: " + part.getString("text"));
                        }
                    }
                }

                // 2. Process turn completion
                if (serverContent.has("turnComplete") && serverContent.getBoolean("turnComplete")) {
                    System.out.println("[DEBUG: GeminiResponseProcessor] Model turn completed (turnComplete = true).");
                }

            } else if (json.has("setup")) {
                System.out.println("[DEBUG: GeminiResponseProcessor] Setup confirmation message received.");
            }

        } catch (Exception e) {
            System.err.println("[ERROR: GeminiResponseProcessor] Critical error parsing JSON message: " + e.getMessage());
            e.printStackTrace();
        }
    }


    /**
     * Extracts and decodes Base64 audio content from an inlineData JSON part.
     * @param audioPart The JSON object containing inlineData.
     */
    private void processAudioPart(JSONObject audioPart) {
        try {
            String base64Audio = audioPart.getJSONObject("inlineData").getString("data");
            System.out.println("[DEBUG: GeminiResponseProcessor] Base64 audio found. Decoding...");

            byte[] audioBytes = Base64.getDecoder().decode(base64Audio);
            System.out.println("[DEBUG: GeminiResponseProcessor] Successfully decoded to " + audioBytes.length + " PCM bytes.");

            audioManager.playAudio(audioBytes);

        } catch (Exception e) {
            System.err.println("[ERROR: GeminiResponseProcessor] Failed to decode Base64 or play audio: " + e.getMessage());
        }
    }
}
