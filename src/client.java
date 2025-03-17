import java.io.*;
import java.net.*;
import java.util.Scanner;
import java.util.Random;

public class client {
    private static final String SERVER_HOST = "127.0.0.1";
    private static final int SERVER_PORT = 5555;
    private static final Random random = new Random();

    public static void main(String[] args) {
        // Launch the GUI version instead of the console version
        VPNGUI.main(args);
    }

    // Helper method to generate traffic data
    public static String generateTrafficData(String destination) {
        int packetSize = random.nextInt(1000) + 100; // Random packet size between 100-1100 bytes
        int protocol = random.nextInt(2); // 0 for TCP, 1 for UDP
        String protocolName = protocol == 0 ? "TCP" : "UDP";
        
        return destination + "|" + protocolName + "|" + packetSize;
    }

    // Helper method to send traffic data
    public static void sendTrafficData(DataOutputStream output, String destination) throws Exception {
        String trafficData = generateTrafficData(destination);
        String encryptedMessage = EncryptionHelper.encrypt(trafficData);
        output.writeInt(encryptedMessage.getBytes().length);
        output.write(encryptedMessage.getBytes());
        output.flush();
    }
}

