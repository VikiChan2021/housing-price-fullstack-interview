package com.example.housing.market.client;

import com.example.housing.market.client.MlApiClient.UpstreamBadGatewayException;
import com.example.housing.market.client.MlApiClient.UpstreamTimeoutException;
import com.example.housing.market.model.PropertyFeatures;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThatThrownBy;

class MlApiClientTest {
    private HttpServer server;

    @AfterEach
    void stopServer() {
        if (server != null) {
            server.stop(0);
        }
    }

    @Test
    void mapsAnUpstreamHttpErrorToBadGateway() throws Exception {
        start(exchange -> respond(exchange, 500, "{}"));

        assertThatThrownBy(() -> client(2).predict(List.of(features()), "request-1"))
                .isInstanceOf(UpstreamBadGatewayException.class)
                .hasMessageContaining("HTTP 500");
    }

    @Test
    void rejectsAnInvalidPredictionCount() throws Exception {
        start(exchange -> respond(exchange, 200,
                "{\"predictions\":[],\"count\":0,\"model_version\":\"test\","
                        + "\"request_id\":\"request-2\"}"));

        assertThatThrownBy(() -> client(2).predict(List.of(features()), "request-2"))
                .isInstanceOf(UpstreamBadGatewayException.class)
                .hasMessageContaining("invalid prediction count");
    }

    @Test
    void mapsAReadTimeoutToGatewayTimeout() throws Exception {
        start(exchange -> {
            try {
                Thread.sleep(1500);
                respond(exchange, 200, "{}");
            } catch (InterruptedException exception) {
                Thread.currentThread().interrupt();
            }
        });

        assertThatThrownBy(() -> client(1).predict(List.of(features()), "request-3"))
                .isInstanceOf(UpstreamTimeoutException.class)
                .hasMessageContaining("timed out");
    }

    private void start(ThrowingHandler handler) throws IOException {
        server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/api/v1/predict", exchange -> {
            try {
                handler.handle(exchange);
            } finally {
                exchange.close();
            }
        });
        server.start();
    }

    private MlApiClient client(long timeoutSeconds) {
        return new MlApiClient("http://127.0.0.1:" + server.getAddress().getPort(),
                timeoutSeconds);
    }

    private static PropertyFeatures features() {
        return new PropertyFeatures(1550.0, 3, 2.0, 1997, 6800.0, 4.1, 7.6);
    }

    private static void respond(HttpExchange exchange, int status, String body) throws IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "application/json");
        exchange.sendResponseHeaders(status, bytes.length);
        exchange.getResponseBody().write(bytes);
    }

    @FunctionalInterface
    private interface ThrowingHandler {
        void handle(HttpExchange exchange) throws IOException;
    }
}
