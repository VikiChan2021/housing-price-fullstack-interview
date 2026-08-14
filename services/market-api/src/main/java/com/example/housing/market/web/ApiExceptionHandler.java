package com.example.housing.market.web;

import com.example.housing.market.client.MlApiClient.UpstreamBadGatewayException;
import com.example.housing.market.client.MlApiClient.UpstreamTimeoutException;
import com.example.housing.market.client.MlApiClient.UpstreamUnavailableException;
import com.example.housing.market.data.DatasetRepository.DatasetNotReadyException;
import com.example.housing.market.model.ApiModels.ErrorBody;
import com.example.housing.market.model.ApiModels.ErrorDetail;
import com.example.housing.market.model.ApiModels.ErrorEnvelope;
import com.example.housing.market.service.ExportService.ExportFailedException;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.List;

@RestControllerAdvice
public class ApiExceptionHandler {
    @ExceptionHandler(IllegalArgumentException.class)
    ResponseEntity<ErrorEnvelope> validation(IllegalArgumentException exception,
                                             HttpServletRequest request) {
        return error(HttpStatus.UNPROCESSABLE_ENTITY, "VALIDATION_ERROR", exception.getMessage(),
                List.of(), request);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    ResponseEntity<ErrorEnvelope> bodyValidation(MethodArgumentNotValidException exception,
                                                 HttpServletRequest request) {
        List<ErrorDetail> details = exception.getBindingResult().getFieldErrors().stream()
                .map(error -> new ErrorDetail(error.getField(), error.getDefaultMessage()))
                .toList();
        return error(HttpStatus.UNPROCESSABLE_ENTITY, "VALIDATION_ERROR",
                "One or more fields are invalid.", details, request);
    }

    @ExceptionHandler(DatasetNotReadyException.class)
    ResponseEntity<ErrorEnvelope> dataset(DatasetNotReadyException exception,
                                          HttpServletRequest request) {
        return error(HttpStatus.SERVICE_UNAVAILABLE, "DATASET_NOT_READY", exception.getMessage(),
                List.of(), request);
    }

    @ExceptionHandler(UpstreamTimeoutException.class)
    ResponseEntity<ErrorEnvelope> timeout(UpstreamTimeoutException exception,
                                          HttpServletRequest request) {
        return error(HttpStatus.GATEWAY_TIMEOUT, "UPSTREAM_TIMEOUT", exception.getMessage(),
                List.of(), request);
    }

    @ExceptionHandler(UpstreamUnavailableException.class)
    ResponseEntity<ErrorEnvelope> unavailable(UpstreamUnavailableException exception,
                                              HttpServletRequest request) {
        return error(HttpStatus.SERVICE_UNAVAILABLE, "UPSTREAM_UNAVAILABLE", exception.getMessage(),
                List.of(), request);
    }

    @ExceptionHandler(UpstreamBadGatewayException.class)
    ResponseEntity<ErrorEnvelope> badGateway(UpstreamBadGatewayException exception,
                                             HttpServletRequest request) {
        return error(HttpStatus.BAD_GATEWAY, "UPSTREAM_UNAVAILABLE", exception.getMessage(),
                List.of(), request);
    }

    @ExceptionHandler(ExportFailedException.class)
    ResponseEntity<ErrorEnvelope> export(ExportFailedException exception,
                                         HttpServletRequest request) {
        return error(HttpStatus.INTERNAL_SERVER_ERROR, "EXPORT_FAILED", exception.getMessage(),
                List.of(), request);
    }

    private static ResponseEntity<ErrorEnvelope> error(HttpStatus status, String code, String message,
                                                        List<ErrorDetail> details,
                                                        HttpServletRequest request) {
        ErrorEnvelope envelope = new ErrorEnvelope(new ErrorBody(code, message, details,
                RequestIdFilter.requestId(request)));
        return ResponseEntity.status(status).body(envelope);
    }
}
