package io.github.giulio_luiz_valcanaia.input;

import io.github.giulio_luiz_valcanaia.client.GeminiLiveClient;

public class InputController {
    
    private static final long LOCK_THRESHOLD_MS = 500;

    private final GeminiLiveClient geminiLiveClient;

    private long pressStartTime = 0; 
    private volatile boolean isLocked = false; 

    public InputController(GeminiLiveClient geminiLiveClient) {
        this.geminiLiveClient = geminiLiveClient;
    }

    public void audioPressedDown() {
        if (pressStartTime != 0) {
            return;
        }

        pressStartTime = System.currentTimeMillis();
        System.out.println("[DEBUG: InputController] Button pressed down with startTime 0");
        isLocked = false;
        
        startMicLoop();
    }

    public void audioPressedUp() {
        if (isLocked) {
            stopMicLoop();
            pressStartTime = 0;
        } else {
            Long clickedTime = System.currentTimeMillis() - pressStartTime;
            if (clickedTime < LOCK_THRESHOLD_MS) {
                System.out.println("[DEBUG: InputController] IsLocked now");
                isLocked = true;
            } else {
                stopMicLoop();
                pressStartTime = 0;
            }
        }
    }

    private void startMicLoop() {
        System.out.println("[DEBUG: InputController] AudioLoop Started");
        geminiLiveClient.startAudioCapture();
    }

    private void stopMicLoop() {
        System.out.println("[DEBUG: InputController] AudioLoop Stoped");
        geminiLiveClient.stopAudioCapture();
    }
}