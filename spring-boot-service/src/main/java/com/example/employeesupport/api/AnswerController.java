package com.example.employeesupport.api;

import com.example.employeesupport.client.PythonClient;
import com.example.employeesupport.model.AnswerRequest;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.RestClientResponseException;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;

@RestController
public class AnswerController {

    private final PythonClient python;

    public AnswerController(PythonClient python) {
        this.python = python;
    }

    @PostMapping("/answer")
    public ResponseEntity<String> answer(
            @RequestHeader(value = "X-Caller-Id", required = false) String callerId,
            @RequestBody AnswerRequest request) {

        if (callerId == null || callerId.isBlank()) {
            return ResponseEntity.badRequest()
                    .body("{\"error\":\"MISSING_CALLER_ID\"}");
        }

        if (request == null ||
                request.question() == null ||
                request.question().isBlank()) {
            return ResponseEntity.badRequest()
                    .body("{\"error\":\"INVALID_REQUEST\"}");
        }

        if (request.as_of() == null || request.as_of().isBlank()) {
            return ResponseEntity.badRequest()
                    .body("{\"error\":\"INVALID_AS_OF\"}");
        }

        try {
            LocalDate.parse(request.as_of());
        } catch (Exception e) {
            return ResponseEntity.badRequest()
                    .body("{\"error\":\"INVALID_AS_OF\"}");
        }

        return ResponseEntity.ok(
                python.answer(callerId, request)
        );
    }

    @ExceptionHandler(RestClientResponseException.class)
    public ResponseEntity<String> downstreamError(RestClientResponseException ex) {
        return ResponseEntity
                .status(HttpStatusCode.valueOf(ex.getStatusCode().value()))
                .body(ex.getResponseBodyAsString());
    }
}
