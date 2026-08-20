package com.example.housing.market.web;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.UUID;

/**
 * Establishes one canonical request ID before controller or exception-handler code runs.
 * Extending {@link OncePerRequestFilter} prevents the same logical request from being assigned a
 * different ID when Spring performs an internal dispatch.
 */
@Component
public class RequestIdFilter extends OncePerRequestFilter {
    // A namespaced servlet attribute avoids collisions with attributes owned by other filters.
    public static final String ATTRIBUTE = RequestIdFilter.class.getName() + ".requestId";

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        String requestId = validOrNew(request.getHeader("X-Request-ID"));
        // Store the ID for server-side consumers and echo it for client-side correlation.
        request.setAttribute(ATTRIBUTE, requestId);
        response.setHeader("X-Request-ID", requestId);
        filterChain.doFilter(request, response);
    }

    private static String validOrNew(String supplied) {
        try {
            // Parsing and rendering the UUID rejects arbitrary text and produces canonical casing.
            return supplied == null ? UUID.randomUUID().toString() : UUID.fromString(supplied).toString();
        } catch (IllegalArgumentException exception) {
            // An invalid caller value must not prevent the request from being handled or traced.
            return UUID.randomUUID().toString();
        }
    }

    public static String requestId(HttpServletRequest request) {
        Object value = request.getAttribute(ATTRIBUTE);
        // The fallback also makes direct unit invocations safe when the filter was not executed.
        return value == null ? UUID.randomUUID().toString() : value.toString();
    }
}
