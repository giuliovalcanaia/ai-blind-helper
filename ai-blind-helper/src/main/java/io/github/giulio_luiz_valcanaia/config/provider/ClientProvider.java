package io.github.giulio_luiz_valcanaia.config.provider;

import java.net.URI;

import io.github.giulio_luiz_valcanaia.client.GeminiLiveClient;

public final class ClientProvider {
    private final GeminiLiveClient geminiLiveClient;

    public ClientProvider(URI uri) {
        try { this.geminiLiveClient = new GeminiLiveClient(uri); } catch (Exception e) { e.printStackTrace(); throw new RuntimeException();};
    }

    public GeminiLiveClient getGeminiLiveClient() { return geminiLiveClient; }
}
