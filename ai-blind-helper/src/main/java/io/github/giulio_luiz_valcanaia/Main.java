package io.github.giulio_luiz_valcanaia;

import java.io.InputStream;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.Properties;

import javax.swing.SwingUtilities;

import io.github.giulio_luiz_valcanaia.client.GeminiLiveClient;
import io.github.giulio_luiz_valcanaia.config.provider.ClientProvider;
import io.github.giulio_luiz_valcanaia.config.provider.ControllerProvider;
import io.github.giulio_luiz_valcanaia.input.KeyboardListener;

public class Main {
    private static final String PROPERTIES_FILE = "config.properties";
    private static final String API_KEY_PROPERTY_NAME = "api.key";
    private static final String HOST = "wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent";

    public static void main(String[] args) {

        String apiKey = loadApiKey();
        URI uri;
        try { 
            uri = new URI(HOST + "?key=" + apiKey); 
        } catch (URISyntaxException e) {
            System.err.println("FATAL ERROR: Invalid host or API key caused URI syntax error.");
            e.printStackTrace();
            System.exit(1);
            return;
        }

        ClientProvider clientProvider = new ClientProvider(uri);
        ControllerProvider controllerProvider = new ControllerProvider(clientProvider);

        // Check if API key was loaded successfully
        if (apiKey == null) {
            System.err.println("FATAL ERROR: API key could not be loaded or is empty.");
            System.exit(1);
            return;
        }
        
        GeminiLiveClient client = clientProvider.getGeminiLiveClient();
        System.out.println("[DEBUG: Main] Client created");
        client.connect();

        // After connect, the keyboard listener is instanciated
        SwingUtilities.invokeLater(() -> new KeyboardListener(controllerProvider.getInputController()));

    }

    /**
     * Loads the API key from the config.properties file.
     * @return The API key or null if loading fails.
     */
    private static String loadApiKey() {
        Properties prop = new Properties();

        try (InputStream input = Main.class.getClassLoader().getResourceAsStream(PROPERTIES_FILE)) {

            if (input == null) {
                System.err.println("ERROR: The file '" + PROPERTIES_FILE + "' was not found. Ensure it is located in src/main/resources.");
                return null;
            }

            prop.load(input);
            String apiKey = prop.getProperty(API_KEY_PROPERTY_NAME);

            if (apiKey == null || apiKey.trim().isEmpty()) {
                System.err.println("ERROR: The property '" + API_KEY_PROPERTY_NAME + "' is missing or empty in the file.");
                return null;
            }
            
            System.out.println("[DEBUG: Main] API key successfully loaded.");
            return apiKey.trim();

        } catch (Exception e) {
            System.err.println("ERROR reading file " + PROPERTIES_FILE + ": " + e.getMessage());
            return null;
        }
    }
}
