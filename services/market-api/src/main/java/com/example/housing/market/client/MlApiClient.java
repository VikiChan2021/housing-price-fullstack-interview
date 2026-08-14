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

@Component
public class MlApiClient {
    private final RestClient client;

    public MlApiClient(@Value("${ml-api.base-url}") String baseUrl,
                       @Value("${ml-api.timeout-seconds}") long timeoutSeconds) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(Duration.ofSeconds(timeoutSeconds));
        factory.setReadTimeout(Duration.ofSeconds(timeoutSeconds));
        this.client = RestClient.builder().baseUrl(baseUrl).requestFactory(factory).build();
    }

    public PredictionResponse predict(List<PropertyFeatures> properties, String requestId) {
        try {
            PredictionResponse response = client.post().uri("/api/v1/predict")
                    .header("X-Request-ID", requestId)
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(properties)
                    .retrieve()
                    .body(PredictionResponse.class);
            if (response == null || response.predictions() == null
                    || response.predictions().size() != properties.size()
                    || response.count() != properties.size()) {
                throw new UpstreamBadGatewayException("ML API returned an invalid prediction count");
            }
            for (int index = 0; index < response.predictions().size(); index++) {
                if (response.predictions().get(index).index() != index) {
                    throw new UpstreamBadGatewayException("ML API returned predictions out of order");
                }
            }
            return response;
        } catch (RestClientResponseException exception) {
            throw new UpstreamBadGatewayException(
                    "ML API returned HTTP " + exception.getStatusCode().value(), exception);
        } catch (ResourceAccessException exception) {
            if (hasTimeoutCause(exception)) {
                throw new UpstreamTimeoutException("ML API request timed out", exception);
            }
            throw new UpstreamUnavailableException("ML API is unavailable", exception);
        } catch (RestClientException exception) {
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
            return false;
        }
    }

    private static boolean hasTimeoutCause(Throwable throwable) {
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
