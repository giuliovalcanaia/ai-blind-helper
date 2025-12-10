package io.github.giulio_luiz_valcanaia.input;

import java.lang.Runnable;

/**
 * Representa uma ação (botão) mapeada para uma tecla específica.
 */
public class KeyAction {
    private final int keyCode;
    private final Runnable actionUp;
    private final Runnable actionDown;
    private final String name; 

    public KeyAction(int keyCode, Runnable actionUp, Runnable actionDown, String name) {
        this.keyCode = keyCode;
        this.actionUp = actionUp;
        this.actionDown = actionDown;
        this.name = name;
    }

    public int getKeyCode() {return keyCode;}
    public String getName() {return name;}

    public void executeOnUp() {
        actionUp.run();
    }

    public void executeOnDown() {
        actionDown.run();
    }
}