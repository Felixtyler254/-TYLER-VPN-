 import java.io.*;
import java.net.*;

public class client {
    public static void main(String[] args) {
        try (Socket socket = new Socket("127.0.0.1", 5555)) {
            System.out.println("Connected to VPN server");

            OutputStream output = socket.getOutputStream();
            InputStream input = socket.getInputStream();

            String message = "Hello from Client!";
            output.write(message.getBytes());
            output.flush();

            byte[] buffer = new byte[1024];
            int bytesRead = input.read(buffer);

            System.out.println("Server response: " + new String(buffer, 0, bytesRead));
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}

