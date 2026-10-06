package com.example.employeesupport.api;

import com.example.employeesupport.client.PythonClient;
import org.junit.jupiter.api.Test;
import org.springframework.http.ResponseEntity;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.multipart.MultipartFile;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

class BatchControllerTest {

    @Test
    void missingCallerIdReturnsBadRequest() {

        PythonClient python = mock(PythonClient.class);

        BatchController controller =
                new BatchController(python);

        MultipartFile file =
                new MockMultipartFile(
                        "files",
                        "request-01.txt",
                        "text/plain",
                        "test".getBytes()
                );

        ResponseEntity<String> response =
                controller.batches(
                        null,
                        "{\"batch_id\":\"batch-001\"}",
                        new MultipartFile[]{file}
                );

        assertEquals(400, response.getStatusCode().value());

        verifyNoInteractions(python);
    }

    @Test
    void missingMetadataReturnsBadRequest() {

        PythonClient python = mock(PythonClient.class);

        BatchController controller =
                new BatchController(python);

        MultipartFile file =
                new MockMultipartFile(
                        "files",
                        "request-01.txt",
                        "text/plain",
                        "test".getBytes()
                );

        ResponseEntity<String> response =
                controller.batches(
                        "atlas-employee-01",
                        "",
                        new MultipartFile[]{file}
                );

        assertEquals(400, response.getStatusCode().value());

        verifyNoInteractions(python);
    }

    @Test
    void missingFilesReturnsBadRequest() {

        PythonClient python = mock(PythonClient.class);

        BatchController controller =
                new BatchController(python);

        ResponseEntity<String> response =
                controller.batches(
                        "atlas-employee-01",
                        "{\"batch_id\":\"batch-001\"}",
                        new MultipartFile[]{}
                );

        assertEquals(400, response.getStatusCode().value());

        verifyNoInteractions(python);
    }

    @Test
    void validBatchIsForwardedToPython() {

        PythonClient python = mock(PythonClient.class);

        when(
                python.batch(
                        anyString(),
                        anyString(),
                        any(MultipartFile[].class)
                )
        ).thenReturn(
                "{\"batch_id\":\"batch-001\",\"summary\":{\"total\":1}}"
        );

        BatchController controller =
                new BatchController(python);

        MultipartFile file =
                new MockMultipartFile(
                        "files",
                        "request-01.txt",
                        "text/plain",
                        "Reference: CERT-101\n"
                                .getBytes()
                );

        String metadata =
                "{\"batch_id\":\"batch-001\","
                        + "\"as_of\":\"2026-09-21\","
                        + "\"documents\":["
                        + "{\"document_id\":\"request-01\","
                        + "\"filename\":\"request-01.txt\"}"
                        + "]}";

        ResponseEntity<String> response =
                controller.batches(
                        "atlas-employee-01",
                        metadata,
                        new MultipartFile[]{file}
                );

        assertEquals(200, response.getStatusCode().value());

        assertNotNull(response.getBody());

        verify(python).batch(
                eq("atlas-employee-01"),
                eq(metadata),
                any(MultipartFile[].class)
        );
    }
}