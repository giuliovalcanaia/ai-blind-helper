package io.github.giulio_luiz_valcanaia.protocol;

import org.json.JSONObject;
import java.util.Base64;

/**
 * Responsibility: Encode JSON messages to be sent to the Gemini Live API
 * over WebSocket, following the API protocol.
 * This class is pure logic — it does not interact with WebSocket or audio hardware.
 */
public class GeminiProtocolEncoder {

    /**
     * Creates the initial session SETUP message (BidiGenerateContentSetup).
     * @return JSON string containing the setup message.
     */
    public String createSetupMessage() {
        return """
            {
                "setup":
                {
                    "generationConfig":
                    {
                        "responseModalities": ["AUDIO"],
                        "mediaResolution": "MEDIA_RESOLUTION_MEDIUM",
                        "speechConfig": 
                        {
                            "voiceConfig": 
                            {
                                "prebuiltVoiceConfig": 
                                {
                                    "voiceName": "Zephyr"
                                }
                            }
                        }
                    },
                    "model": "models/gemini-2.5-flash-native-audio-preview-09-2025"
                }
            }
            """;
    }

    /**
     * Creates a RealtimeInput message that contains a chunk of raw PCM audio.
     * @param audioData Raw PCM chunk captured from the microphone.
     * @param mimeType The audio MIME type (e.g., audio/pcm;rate=16000).
     * @return JSON string containing the realtime input message.
     */
    public String createAudioInputMessage(byte[] audioData, String mimeType) {
        String base64Audio = Base64.getEncoder().encodeToString(audioData);

        JSONObject audioBlob = new JSONObject();
        audioBlob.put("data", base64Audio);
        audioBlob.put("mimeType", mimeType);

        JSONObject realtimeInput = new JSONObject();
        realtimeInput.put("audio", audioBlob);

        JSONObject payload = new JSONObject();
        payload.put("realtimeInput", realtimeInput);

        return payload.toString();
    }
}
