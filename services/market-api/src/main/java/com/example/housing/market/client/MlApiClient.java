package com.example.housing.market.client;

import com.example.housing.market.model.ApiModels.RangeWarning;
import com.example.housing.market.model.PropertyFeatures;
import com.fasterxml.jackson.annotation.JsonProperty;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestClientResponseException;

import java.net.SocketTimeoutException;
import java.time.Duration;
import java.util.List;

/**
 * Owns all HTTP communication with the ML API and translates transport failures into domain
 * exceptions understood by the global API exception handler.
 */
@Component
public class MlApiClient {
    private final RestClient client;

    public MlApiClient(@Value("${ml-api.base-url}") String baseUrl,
                       @Value("${ml-api.timeout-seconds}") long timeoutSeconds) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        // Bound both connection establishment and response reading to avoid hanging request threads.
        factory.setConnectTimeout(Duration.ofSeconds(timeoutSeconds));
        factory.setReadTimeout(Duration.ofSeconds(timeoutSeconds));
        this.client = RestClient.builder().baseUrl(baseUrl).requestFactory(factory).build();
    }

    public PredictionResponse predict(List<PropertyFeatures> properties, String requestId) {
        try {
            // A batch preserves baseline/scenario ordering and avoids two independently failing calls.
            PredictionResponse response = client.post().uri("/api/v1/predict")
                    .header("X-Request-ID", requestId)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(properties)
                    .retrieve()
                    .body(PredictionResponse.class);
            // Treat a syntactically valid but incomplete body as a dependency contract violation.
            if (response == null || response.predictions() == null
                    || response.predictions().size() != properties.size()
                    || response.count() != properties.size()) {
                throw new UpstreamBadGatewayException("ML API returned an invalid prediction count");
            }
            for (int index = 0; index < response.predictions().size(); index++) {
                // The explicit index protects callers from silently pairing a price with the wrong input.
                if (response.predictions().get(index).index() != index) {
                    throw new UpstreamBadGatewayException("ML API returned predictions out of order");
                }
            }
            return response;
        } catch (RestClientResponseException exception) {
            // Non-2xx responses prove connectivity but not a usable dependency response.
            throw new UpstreamBadGatewayException(
                    "ML API returned HTTP " + exception.getStatusCode().value(), exception);
        } catch (ResourceAccessException exception) {
            if (hasTimeoutCause(exception)) {
                throw new UpstreamTimeoutException("ML API request timed out", exception);
            }
            throw new UpstreamUnavailableException("ML API is unavailable", exception);
        } catch (RestClientException exception) {
            if (hasTimeoutCause(exception)) {
                throw new UpstreamTimeoutException("ML API request timed out", exception);
            }
            throw new UpstreamBadGatewayException("ML API returned an invalid response", exception);
        }
    }

    public boolean health() {
        return probe("/health");
    }

    public boolean ready() {
        return probe("/ready");
    }

    private boolean probe(String path) {
        try {
            return client.get().uri(path).retrieve().toBodilessEntity().getStatusCode().is2xxSuccessful();
        } catch (RestClientException exception) {
            // Probe endpoints intentionally collapse transport details into a boolean status.
            return false;
        }
    }

    private static boolean hasTimeoutCause(Throwable throwable) {
        // Spring may wrap the socket timeout several levels deep; inspect the full cause chain.
        Throwable current = throwable;
        while (current != null) {
            if (current instanceof SocketTimeoutException
                    || current.getClass().getSimpleName().toLowerCase().contains("timeout")) {
                return true;
            }
            current = current.getCause();
        }
        return false;
    }

    public record PredictionItem(int index,
                                 @JsonProperty("predicted_price") double predictedPrice,
                                 List<RangeWarning> warnings) {
    }

    // Records provide immutable, constructor-based JSON transport objects with minimal boilerplate.
    public record PredictionResponse(List<PredictionItem> predictions, int count,
                                     @JsonProperty("model_version") String modelVersion,
                                     @JsonProperty("request_id") String requestId) {
    }

    public static class UpstreamTimeoutException extends RuntimeException {
        public UpstreamTimeoutException(String message, Throwable cause) {
            super(message, cause);
        }
    }

    public static class UpstreamUnavailableException extends RuntimeException {
        public UpstreamUnavailableException(String message, Throwable cause) {
            super(message, cause);
        }
    }

    public static class UpstreamBadGatewayException extends RuntimeException {
        public UpstreamBadGatewayException(String message) {
            super(message);
        }

        public UpstreamBadGatewayException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
