package io.github.giulio_luiz_valcanaia.input;

import javax.swing.JFrame;
import java.awt.event.KeyEvent;
import java.awt.event.KeyListener;
import java.util.HashMap;
import java.util.Map; // Importe o Map e o HashMap

// Seu KeyboardListener refatorado
public class KeyboardListener extends JFrame implements KeyListener {

    private final InputController inputController;
    private final Map<Integer, KeyAction> keyActionsMap = new HashMap<>();

    public KeyboardListener(InputController inputController) {
        this.inputController = inputController; 

        setTitle("Leitor de Teclas Mapeadas");
        setSize(400, 300);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        
        // Configuração do KeyListener e Foco
        addKeyListener(this);
        setFocusable(true);
        requestFocusInWindow(); 
        
        // Chamamos o método para configurar as ações (ver próxima seção)
        setupKeyActions(); 
        setVisible(true);
    }

    
    
    @Override
    public void keyPressed(KeyEvent e) {
        int keyCode = e.getKeyCode();
        
        if (keyActionsMap.containsKey(keyCode)) {
            KeyAction action = keyActionsMap.get(keyCode);
            action.executeOnDown();
        } else {
            System.out.println("Pressionada: Tecla não mapeada: " + KeyEvent.getKeyText(keyCode));
        }
    }

    @Override
    public void keyReleased(KeyEvent e) {
        int keyCode = e.getKeyCode();
        
        if (keyActionsMap.containsKey(keyCode)) {
            KeyAction action = keyActionsMap.get(keyCode);
            action.executeOnUp();
        } else {
            System.out.println("Solta: Código=" + keyCode + " | Nome=" + KeyEvent.getKeyText(keyCode));
        }
    }
    
    @Override
    public void keyTyped(KeyEvent e) {}
    
    // O setupKeyActions deve apenas mapear a tecla, a lógica será tratada no Controller
    private void setupKeyActions() {
        // A ação interna (Runnable) não precisa mais chamar o Controller,
        // pois o Controller será chamado diretamente em keyPressed/keyReleased
        addAction(new KeyAction(
            KeyEvent.VK_A, 
            () -> { inputController.audioPressedUp(); }, 
            () -> { inputController.audioPressedDown(); },
            "AudioControl"
        ));
    }

    public void addAction(KeyAction action) {
        keyActionsMap.put(action.getKeyCode(), action);
        System.out.println("Mapeada a ação: " + action.getName() + " para o código: " + action.getKeyCode());
    }
}