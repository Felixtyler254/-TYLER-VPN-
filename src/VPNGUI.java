import javax.swing.*;
import java.awt.*;
import java.awt.event.*;
import java.io.*;
import java.net.*;
import java.util.Random;

public class VPNGUI extends JFrame {
    private JButton connectButton;
    private JButton disconnectButton;
    private JTextArea statusArea;
    private JTextField destinationField;
    private JLabel statusLabel;
    private JProgressBar trafficBar;
    private Socket socket;
    private DataInputStream input;
    private DataOutputStream output;
    private boolean isConnected = false;
    private final Random random = new Random();
    private Timer trafficTimer;

    public VPNGUI() {
        setTitle("AI-Enhanced VPN Client");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(600, 400);
        setLocationRelativeTo(null);

        // Create main panel
        JPanel mainPanel = new JPanel(new BorderLayout(10, 10));
        mainPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        // Create connection panel
        JPanel connectionPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        connectButton = new JButton("Connect");
        disconnectButton = new JButton("Disconnect");
        disconnectButton.setEnabled(false);
        connectionPanel.add(connectButton);
        connectionPanel.add(disconnectButton);

        // Create destination panel
        JPanel destinationPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        destinationPanel.add(new JLabel("Destination:"));
        destinationField = new JTextField("127.0.0.1:5555", 20);
        destinationPanel.add(destinationField);

        // Create status panel
        JPanel statusPanel = new JPanel(new BorderLayout());
        statusLabel = new JLabel("Status: Disconnected");
        statusPanel.add(statusLabel, BorderLayout.NORTH);
        
        statusArea = new JTextArea(10, 40);
        statusArea.setEditable(false);
        JScrollPane scrollPane = new JScrollPane(statusArea);
        statusPanel.add(scrollPane, BorderLayout.CENTER);

        // Create traffic monitoring panel
        JPanel trafficPanel = new JPanel(new BorderLayout());
        trafficPanel.add(new JLabel("Traffic Activity:"), BorderLayout.NORTH);
        trafficBar = new JProgressBar(0, 100);
        trafficBar.setStringPainted(true);
        trafficPanel.add(trafficBar, BorderLayout.CENTER);

        // Add all panels to main panel
        mainPanel.add(connectionPanel, BorderLayout.NORTH);
        mainPanel.add(destinationPanel, BorderLayout.CENTER);
        mainPanel.add(statusPanel, BorderLayout.CENTER);
        mainPanel.add(trafficPanel, BorderLayout.SOUTH);

        // Add main panel to frame
        add(mainPanel);

        // Setup button listeners
        connectButton.addActionListener(e -> connect());
        disconnectButton.addActionListener(e -> disconnect());

        // Setup traffic monitoring timer
        trafficTimer = new Timer(1000, e -> updateTrafficBar());
        trafficTimer.start();
    }

    private void connect() {
        try {
            String[] parts = destinationField.getText().split(":");
            String host = parts[0];
            int port = Integer.parseInt(parts[1]);

            socket = new Socket(host, port);
            input = new DataInputStream(socket.getInputStream());
            output = new DataOutputStream(socket.getOutputStream());

            isConnected = true;
            connectButton.setEnabled(false);
            disconnectButton.setEnabled(true);
            statusLabel.setText("Status: Connected");
            statusArea.append("Connected to VPN server at " + host + ":" + port + "\n");

            // Start receiving thread
            new Thread(this::receiveMessages).start();

        } catch (Exception e) {
            statusArea.append("Connection error: " + e.getMessage() + "\n");
            disconnect();
        }
    }

    private void disconnect() {
        try {
            if (socket != null && !socket.isClosed()) {
                socket.close();
                socket = null;
            }
        } catch (IOException e) {
            statusArea.append("Error disconnecting: " + e.getMessage() + "\n");
        } finally {
            isConnected = false;
            connectButton.setEnabled(true);
            disconnectButton.setEnabled(false);
            statusLabel.setText("Status: Disconnected");
            statusArea.append("Disconnected from VPN server\n");
        }
    }

    private void receiveMessages() {
        try {
            while (isConnected) {
                int dataLength = input.readInt();
                byte[] encryptedData = new byte[dataLength];
                input.readFully(encryptedData);
                
                String decryptedData = EncryptionHelper.decrypt(new String(encryptedData));
                SwingUtilities.invokeLater(() -> {
                    statusArea.append("Server: " + decryptedData + "\n");
                    statusArea.setCaretPosition(statusArea.getDocument().getLength());
                });
            }
        } catch (EOFException e) {
            SwingUtilities.invokeLater(() -> {
                statusArea.append("Server disconnected\n");
                disconnect();
            });
        } catch (Exception e) {
            SwingUtilities.invokeLater(() -> {
                statusArea.append("Error receiving data: " + e.getMessage() + "\n");
                disconnect();
            });
        }
    }

    private void updateTrafficBar() {
        if (isConnected) {
            int traffic = random.nextInt(100);
            trafficBar.setValue(traffic);
            trafficBar.setString(traffic + "%");
        } else {
            trafficBar.setValue(0);
            trafficBar.setString("0%");
        }
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            new VPNGUI().setVisible(true);
        });
    }
} 