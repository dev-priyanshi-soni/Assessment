package com.example.employeesupport.api;

import com.example.employeesupport.client.PythonClient;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
public class BatchController {

    private final PythonClient python;

    public BatchController(PythonClient python) {
        this.python = python;
    }

    @PostMapping(
            value = "/batches",
            consumes = MediaType.MULTIPART_FORM_DATA_VALUE,
            produces = MediaType.APPLICATION_JSON_VALUE
    )
    public ResponseEntity<String> batches(
            @RequestHeader(value = "X-Caller-Id", required = false)
            String callerId,

            @RequestPart("metadata")
            String metadata,

            @RequestPart("files")
            MultipartFile[] files
    ) {

        // ---------------------------------------------------------
        // Public API validation
        // ---------------------------------------------------------

        if (callerId == null || callerId.isBlank()) {
            return ResponseEntity.badRequest()
                    .body("{\"error\":\"MISSING_CALLER_ID\"}");
        }

        if (metadata == null || metadata.isBlank()) {
            return ResponseEntity.badRequest()
                    .body("{\"error\":\"MISSING_METADATA\"}");
        }

        if (files == null || files.length == 0) {
            return ResponseEntity.badRequest()
                    .body("{\"error\":\"MISSING_FILES\"}");
        }

        // ---------------------------------------------------------
        // Delegate batch processing to Python
        // ---------------------------------------------------------

        return ResponseEntity.ok(
                python.batch(
                        callerId,
                        metadata,
                        files
                )
        );
    }
}