package com.example.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/currency")
public class CurrencyConversionController {

    @GetMapping("/convert")
    public ResponseEntity<Map<String, Object>> convertCurrency(
            @RequestParam(defaultValue = "USD") String from,
            @RequestParam(defaultValue = "EUR") String to,
            @RequestParam(defaultValue = "1.0") Double amount) {

        Map<String, Object> response = new HashMap<>();
        response.put("from", from);
        response.put("to", to);
        response.put("amount", amount);
        // Mock conversion rate
        response.put("convertedAmount", amount * 0.92);
        response.put("rate", 0.92);

        return ResponseEntity.ok(response);
    }

    @GetMapping("/hello")
    public ResponseEntity<Map<String, String>> hello() {
        Map<String, String> response = new HashMap<>();
        response.put("message", "Currency Conversion Service is running");
        response.put("status", "OK");
        return ResponseEntity.ok(response);
    }
}
