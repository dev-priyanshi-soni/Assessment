package com.example.employeesupport.api;

import com.example.employeesupport.client.PythonClient;
import com.example.employeesupport.model.AnswerRequest;
import org.junit.jupiter.api.Test;
import org.springframework.http.ResponseEntity;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class AnswerControllerTest {

    @Test
    void missingCallerIdReturnsBadRequest() {

        PythonClient python = mock(PythonClient.class);

        AnswerController controller =
                new AnswerController(python);

        AnswerRequest request =
                new AnswerRequest(
                        "What is the certification limit?",
                        "2026-09-21"
                );

        ResponseEntity<String> response =
                controller.answer(null, request);

        assertEquals(400, response.getStatusCode().value());
        assertEquals(
                "{\"error\":\"MISSING_CALLER_ID\"}",
                response.getBody()
        );

        verifyNoInteractions(python);
    }

    @Test
    void blankQuestionReturnsBadRequest() {

        PythonClient python = mock(PythonClient.class);

        AnswerController controller =
                new AnswerController(python);

        AnswerRequest request =
                new AnswerRequest(
                        "",
                        "2026-09-21"
                );

        ResponseEntity<String> response =
                controller.answer(
                        "atlas-employee-01",
                        request
                );

        assertEquals(400, response.getStatusCode().value());

        verifyNoInteractions(python);
    }

    @Test
    void missingAsOfReturnsBadRequest() {

        PythonClient python = mock(PythonClient.class);

        AnswerController controller =
                new AnswerController(python);

        AnswerRequest request =
                new AnswerRequest(
                        "What is the certification limit?",
                        ""
                );

        ResponseEntity<String> response =
                controller.answer(
                        "atlas-employee-01",
                        request
                );

        assertEquals(400, response.getStatusCode().value());

        verifyNoInteractions(python);
    }

    @Test
    void validRequestIsForwardedToPython() {

        PythonClient python = mock(PythonClient.class);

        when(
                python.answer(
                        eq("atlas-employee-01"),
                        any(AnswerRequest.class)
                )
        ).thenReturn(
                "{\"status\":\"ANSWERED\",\"answer\":\"INR 25000\",\"citations\":[]}"
        );

        AnswerController controller =
                new AnswerController(python);

        AnswerRequest request =
                new AnswerRequest(
                        "What is the certification limit?",
                        "2026-09-21"
                );

        ResponseEntity<String> response =
                controller.answer(
                        "atlas-employee-01",
                        request
                );

        assertEquals(200, response.getStatusCode().value());

        assertNotNull(response.getBody());

        verify(python).answer(
                eq("atlas-employee-01"),
                eq(request)
        );
    }
}