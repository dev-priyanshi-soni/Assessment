// package com.example.employeesupport.client;

// import com.example.employeesupport.model.AnswerRequest;
// import org.springframework.beans.factory.annotation.Value;
// import org.springframework.http.HttpStatusCode;
// import org.springframework.stereotype.Component;
// import org.springframework.web.server.ResponseStatusException;

// import java.io.IOException;
// import java.net.URI;
// import java.net.http.HttpClient;
// import java.net.http.HttpRequest;
// import java.net.http.HttpResponse;
// import java.nio.charset.StandardCharsets;

// @Component
// public class PythonClient {

//     private final HttpClient client;
//     private final URI answerUri;

//     public PythonClient(
//             @Value("${python.service.base-url:http://127.0.0.1:8000}") String baseUrl) {

//         this.client = HttpClient.newHttpClient();
//         this.answerUri = URI.create(baseUrl).resolve("/internal/answer");
//     }

//     public String answer(String callerId, AnswerRequest request) {
//         String jsonBody = String.format(
//                 "{\"question\":\"%s\",\"as_of\":\"%s\"}",
//                 escapeJson(request.question()),
//                 escapeJson(request.as_of())
//         );

//         HttpRequest pythonRequest = HttpRequest.newBuilder(answerUri)
//                 .version(HttpClient.Version.HTTP_1_1)
//                 .header("Content-Type", "application/json")
//                 .header("Accept", "application/json")
//                 .header("X-Caller-Id", callerId)
//                 .POST(HttpRequest.BodyPublishers.ofString(jsonBody, StandardCharsets.UTF_8))
//                 .build();

//         try {
//             HttpResponse<String> response = client.send(
//                     pythonRequest,
//                     HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8)
//             );

//             if (response.statusCode() >= 200 && response.statusCode() < 300) {
//                 return response.body();
//             }

//             throw new ResponseStatusException(
//                     HttpStatusCode.valueOf(response.statusCode()),
//                     response.body()
//             );
//         } catch (IOException e) {
//             throw new ResponseStatusException(
//                     HttpStatusCode.valueOf(502),
//                     "Python service is not reachable",
//                     e
//             );
//         } catch (InterruptedException e) {
//             Thread.currentThread().interrupt();
//             throw new ResponseStatusException(
//                     HttpStatusCode.valueOf(502),
//                     "Python service call was interrupted",
//                     e
//             );
//         }
//     }

//     private String escapeJson(String value) {
//         if (value == null) {
//             return "";
//         }

//         return value
//                 .replace("\\", "\\\\")
//                 .replace("\"", "\\\"")
//                 .replace("\n", "\\n")
//                 .replace("\r", "\\r")
//                 .replace("\t", "\\t");
//     }
// }
package com.example.employeesupport.client;

import com.example.employeesupport.model.AnswerRequest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatusCode;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.util.UUID;

@Component
public class PythonClient {

    private final HttpClient client;
    private final URI answerUri;
    private final URI batchUri;

    public PythonClient(
            @Value("${python.service.base-url:http://127.0.0.1:8000}")
            String baseUrl) {

        this.client = HttpClient.newHttpClient();

        URI baseUri = URI.create(baseUrl);

        this.answerUri = baseUri.resolve("/internal/answer");
        this.batchUri = baseUri.resolve("/internal/batches");
    }

    // ============================================================
    // SINGLE ANSWER
    // ============================================================

    public String answer(
            String callerId,
            AnswerRequest request) {

        String jsonBody = String.format(
                "{\"question\":\"%s\",\"as_of\":\"%s\"}",
                escapeJson(request.question()),
                escapeJson(request.as_of())
        );

        HttpRequest pythonRequest = HttpRequest.newBuilder(answerUri)
                .version(HttpClient.Version.HTTP_1_1)
                .header("Content-Type", "application/json")
                .header("Accept", "application/json")
                .header("X-Caller-Id", callerId)
                .POST(
                        HttpRequest.BodyPublishers.ofString(
                                jsonBody,
                                StandardCharsets.UTF_8
                        )
                )
                .build();

        try {

            HttpResponse<String> response = client.send(
                    pythonRequest,
                    HttpResponse.BodyHandlers.ofString(
                            StandardCharsets.UTF_8
                    )
            );

            if (response.statusCode() >= 200
                    && response.statusCode() < 300) {

                return response.body();
            }

            throw new ResponseStatusException(
                    HttpStatusCode.valueOf(response.statusCode()),
                    response.body()
            );

        } catch (IOException e) {

            throw new ResponseStatusException(
                    HttpStatusCode.valueOf(502),
                    "Python service is not reachable",
                    e
            );

        } catch (InterruptedException e) {

            Thread.currentThread().interrupt();

            throw new ResponseStatusException(
                    HttpStatusCode.valueOf(502),
                    "Python service call was interrupted",
                    e
            );
        }
    }

    // ============================================================
    // BATCH
    // ============================================================

    public String batch(
            String callerId,
            String metadata,
            MultipartFile[] files) {

        String boundary =
                "----MarlabsBoundary" + UUID.randomUUID();

        try {

            byte[] multipartBody =
                    buildMultipartBody(
                            boundary,
                            metadata,
                            files
                    );

            HttpRequest pythonRequest =
                    HttpRequest.newBuilder(batchUri)
                            .version(HttpClient.Version.HTTP_1_1)
                            .header(
                                    "Content-Type",
                                    "multipart/form-data; boundary="
                                            + boundary
                            )
                            .header(
                                    "Accept",
                                    "application/json"
                            )
                            .header(
                                    "X-Caller-Id",
                                    callerId
                            )
                            .POST(
                                    HttpRequest.BodyPublishers.ofByteArray(
                                            multipartBody
                                    )
                            )
                            .build();

            HttpResponse<String> response =
                    client.send(
                            pythonRequest,
                            HttpResponse.BodyHandlers.ofString(
                                    StandardCharsets.UTF_8
                            )
                    );

            if (response.statusCode() >= 200
                    && response.statusCode() < 300) {

                return response.body();
            }

            throw new ResponseStatusException(
                    HttpStatusCode.valueOf(response.statusCode()),
                    response.body()
            );

        } catch (IOException e) {

            throw new ResponseStatusException(
                    HttpStatusCode.valueOf(502),
                    "Python batch service is not reachable",
                    e
            );

        } catch (InterruptedException e) {

            Thread.currentThread().interrupt();

            throw new ResponseStatusException(
                    HttpStatusCode.valueOf(502),
                    "Python batch service call was interrupted",
                    e
            );
        }
    }

    // ============================================================
    // MULTIPART BUILDER
    // ============================================================

    private byte[] buildMultipartBody(
            String boundary,
            String metadata,
            MultipartFile[] files) throws IOException {

        ByteArrayOutputStream output =
                new ByteArrayOutputStream();

        String separator = "--" + boundary + "\r\n";

        // --------------------------------------------------------
        // Metadata part
        // --------------------------------------------------------

        output.write(
                separator.getBytes(StandardCharsets.UTF_8)
        );

        output.write(
                (
                        "Content-Disposition: form-data; "
                                + "name=\"metadata\"\r\n"
                                + "Content-Type: application/json\r\n"
                                + "\r\n"
                ).getBytes(StandardCharsets.UTF_8)
        );

        output.write(
                metadata.getBytes(StandardCharsets.UTF_8)
        );

        output.write(
                "\r\n".getBytes(StandardCharsets.UTF_8)
        );

        // --------------------------------------------------------
        // File parts
        // --------------------------------------------------------

        for (MultipartFile file : files) {

            String filename = file.getOriginalFilename();

            if (filename == null || filename.isBlank()) {
                throw new IllegalArgumentException(
                        "Uploaded file must have a filename"
                );
            }

            output.write(
                    separator.getBytes(StandardCharsets.UTF_8)
            );

            output.write(
                    (
                            "Content-Disposition: form-data; "
                                    + "name=\"files\"; "
                                    + "filename=\""
                                    + sanitizeFilename(filename)
                                    + "\"\r\n"
                                    + "Content-Type: "
                                    + resolveContentType(file)
                                    + "\r\n"
                                    + "\r\n"
                    ).getBytes(StandardCharsets.UTF_8)
            );

            output.write(file.getBytes());

            output.write(
                    "\r\n".getBytes(StandardCharsets.UTF_8)
            );
        }

        // --------------------------------------------------------
        // Closing boundary
        // --------------------------------------------------------

        output.write(
                (
                        "--"
                                + boundary
                                + "--\r\n"
                ).getBytes(StandardCharsets.UTF_8)
        );

        return output.toByteArray();
    }

    // ============================================================
    // CONTENT TYPE
    // ============================================================

    private String resolveContentType(
            MultipartFile file) {

        String contentType = file.getContentType();

        if (contentType != null
                && !contentType.isBlank()) {

            return contentType;
        }

        String filename = file.getOriginalFilename();

        if (filename != null) {

            String lower =
                    filename.toLowerCase();

            if (lower.endsWith(".pdf")) {
                return "application/pdf";
            }

            if (lower.endsWith(".txt")) {
                return "text/plain";
            }
        }

        return "application/octet-stream";
    }

    // ============================================================
    // FILENAME SANITIZATION
    // ============================================================

    private String sanitizeFilename(
            String filename) {

        return filename
                .replace("\\", "_")
                .replace("\"", "_")
                .replace("\r", "_")
                .replace("\n", "_");
    }

    // ============================================================
    // JSON ESCAPING
    // ============================================================

    private String escapeJson(String value) {

        if (value == null) {
            return "";
        }

        return value
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t");
    }
}