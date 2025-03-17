import java.io.*;
import java.net.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class Main {
    private static final int SERVER_PORT = 5555;
    private static final ConcurrentHashMap<String, Socket> connectedClients = new ConcurrentHashMap<>();
    private static final Pattern IP_PORT_PATTERN = Pattern.compile("(\\d+\\.\\d+\\.\\d+\\.\\d+):(\\d+)");

    public static void main(String[] args) {
        try (ServerSocket serverSocket = new ServerSocket(SERVER_PORT)) {
            System.out.println("AI-Enhanced VPN Server is running on port " + SERVER_PORT);
            System.out.println("Traffic analysis and security monitoring enabled");

            while (true) {
                Socket clientSocket = serverSocket.accept();
                String clientId = clientSocket.getInetAddress().getHostAddress() + ":" + clientSocket.getPort();
                System.out.println("New client connected: " + clientId);
                connectedClients.put(clientId, clientSocket);

                new Thread(() -> handleClient(clientSocket, clientId)).start();
            }
        } catch (IOException e) {
            System.err.println("Server error: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private static void handleClient(Socket clientSocket, String clientId) {
        try (
                DataInputStream input = new DataInputStream(clientSocket.getInputStream());
                DataOutputStream output = new DataOutputStream(clientSocket.getOutputStream())
        ) {
            while (true) {
                // Read the length of the incoming data
                int dataLength = input.readInt();
                byte[] encryptedData = new byte[dataLength];
                input.readFully(encryptedData);

                // Decrypt the data
                String decryptedData = EncryptionHelper.decrypt(new String(encryptedData));
                
                // Extract IP and port information from the data
                Matcher matcher = IP_PORT_PATTERN.matcher(decryptedData);
                if (matcher.find()) {
                    String sourceIP = matcher.group(1);
                    int port = Integer.parseInt(matcher.group(2));
                    
                    // Analyze traffic using AI
                    AIHelper.TrafficData trafficData = new AIHelper.TrafficData(
                        dataLength,
                        sourceIP,
                        clientSocket.getInetAddress().getHostAddress(),
                        port
                    );
                    AIHelper.analyzeTraffic(clientId, trafficData);

                    // Check if traffic should be blocked
                    if (AIHelper.shouldBlockTraffic(clientId)) {
                        String blockMessage = "Traffic blocked due to suspicious activity";
                        sendEncryptedResponse(output, blockMessage);
                        continue;
                    }

                    // Get optimal route
                    String optimalRoute = AIHelper.getOptimalRoute(sourceIP, clientSocket.getInetAddress().getHostAddress());
                    decryptedData = "Route: " + optimalRoute + " | " + decryptedData;
                }
                
                // Process the VPN packet
                processVPNPacket(decryptedData, output);
            }
        } catch (EOFException e) {
            System.out.println("Client disconnected: " + clientId);
        } catch (Exception e) {
            System.err.println("Error handling client " + clientId + ": " + e.getMessage());
            e.printStackTrace();
        } finally {
            connectedClients.remove(clientId);
            AIHelper.cleanupClientData(clientId);
            try {
                clientSocket.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    private static void processVPNPacket(String data, DataOutputStream output) throws Exception {
        String response = "Server processed: " + data;
        sendEncryptedResponse(output, response);
    }

    private static void sendEncryptedResponse(DataOutputStream output, String response) throws Exception {
        String encryptedResponse = EncryptionHelper.encrypt(response);
        output.writeInt(encryptedResponse.getBytes().length);
        output.write(encryptedResponse.getBytes());
        output.flush();
    }
}
