package io.github.giulio_luiz_valcanaia.config.provider;

import io.github.giulio_luiz_valcanaia.input.InputController;

public class ControllerProvider {
    private final InputController inputController;

    public ControllerProvider(ClientProvider clientProvider) {
        this.inputController = new InputController(clientProvider.getGeminiLiveClient());
    }

    public InputController getInputController() { return inputController; }
}
