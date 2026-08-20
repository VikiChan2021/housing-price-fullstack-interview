package com.example.housing.market;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class MarketApiApplication {

    /**
     * Starts the Spring application context and the embedded HTTP server.
     * {@code @SpringBootApplication} also enables auto-configuration and component scanning
     * below this package, so controllers, services, clients, and filters are discovered without
     * an explicit registration list.
     */
    public static void main(String[] args) {
        SpringApplication.run(MarketApiApplication.class, args);
    }
}
