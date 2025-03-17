import java.util.*;
import java.time.*;
import java.util.concurrent.ConcurrentHashMap;

public class AIHelper {
    private static final Map<String, List<TrafficData>> clientTrafficHistory = new ConcurrentHashMap<>();
    private static final Map<String, Double> clientRiskScores = new ConcurrentHashMap<>();
    private static final int MAX_HISTORY_SIZE = 1000;
    private static final double RISK_THRESHOLD = 0.7;

    public static class TrafficData {
        public final long timestamp;
        public final int packetSize;
        public final String sourceIP;
        public final String destinationIP;
        public final int port;

        public TrafficData(int packetSize, String sourceIP, String destinationIP, int port) {
            this.timestamp = System.currentTimeMillis();
            this.packetSize = packetSize;
            this.sourceIP = sourceIP;
            this.destinationIP = destinationIP;
            this.port = port;
        }
    }

    public static void analyzeTraffic(String clientId, TrafficData data) {
        clientTrafficHistory.computeIfAbsent(clientId, k -> new ArrayList<>()).add(data);
        
        // Keep only recent history
        List<TrafficData> history = clientTrafficHistory.get(clientId);
        if (history.size() > MAX_HISTORY_SIZE) {
            history.remove(0);
        }

        // Calculate risk score
        double riskScore = calculateRiskScore(clientId);
        clientRiskScores.put(clientId, riskScore);

        // Log suspicious activity
        if (riskScore > RISK_THRESHOLD) {
            System.out.println("WARNING: Suspicious activity detected from client " + clientId);
            System.out.println("Risk score: " + riskScore);
        }
    }

    private static double calculateRiskScore(String clientId) {
        List<TrafficData> history = clientTrafficHistory.get(clientId);
        if (history == null || history.isEmpty()) {
            return 0.0;
        }

        double score = 0.0;
        
        // Analyze packet sizes
        double avgPacketSize = history.stream()
                .mapToInt(d -> d.packetSize)
                .average()
                .orElse(0.0);
        
        // Check for unusually large packets
        if (avgPacketSize > 1500) { // Typical MTU size
            score += 0.3;
        }

        // Analyze traffic patterns
        long currentTime = System.currentTimeMillis();
        long recentTraffic = history.stream()
                .filter(d -> currentTime - d.timestamp < 60000) // Last minute
                .count();
        
        // Check for burst traffic
        if (recentTraffic > 100) {
            score += 0.2;
        }

        // Check for suspicious ports
        long suspiciousPorts = history.stream()
                .filter(d -> d.port < 1024 || d.port == 3389 || d.port == 22)
                .count();
        
        if (suspiciousPorts > 0) {
            score += 0.3;
        }

        return Math.min(score, 1.0);
    }

    public static boolean shouldBlockTraffic(String clientId) {
        Double riskScore = clientRiskScores.get(clientId);
        return riskScore != null && riskScore > RISK_THRESHOLD;
    }

    public static String getOptimalRoute(String sourceIP, String destinationIP) {
        // Simple routing logic based on network conditions
        // In a real implementation, this would use more sophisticated algorithms
        return "10.0.0.1"; // Default route
    }

    public static void cleanupClientData(String clientId) {
        clientTrafficHistory.remove(clientId);
        clientRiskScores.remove(clientId);
    }
} 