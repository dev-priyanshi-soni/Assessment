from datetime import date
from pathlib import Path
import tempfile
from fastapi import FastAPI, Header, HTTPException, UploadFile, File, Form
from .caller import get_caller
from .models import AnswerRequest, AnswerResponse, BatchMetadata
from .policy import PolicyStore
from .workflow import AnswerWorkflow
from .batch import BatchProcessor

app = FastAPI(title="Marlabs Python Policy Service", version="1.0.0")
store = PolicyStore()
workflow = AnswerWorkflow(store)
processor = BatchProcessor(workflow)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/internal/answer", response_model=AnswerResponse)
def answer(req: AnswerRequest, x_caller_id: str = Header(...)):
    try:
        caller = get_caller(x_caller_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Unknown caller")
    return workflow.run(req.question, req.as_of, caller)

@app.post("/internal/batches")
async def batches(
    metadata: str = Form(...),
    files: list[UploadFile] = File(...)
):
    import json

    data = BatchMetadata.model_validate(json.loads(metadata))

    try:
        caller = get_caller("atlas-employee-01")
    except ValueError:
        raise HTTPException(status_code=401, detail="Unknown caller")

    with tempfile.TemporaryDirectory() as td:
        paths = {}

        for f in files:
            if not f.filename or not f.filename.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Every uploaded file must have a filename"
                )

            filename = Path(f.filename).name

            if not filename:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid uploaded filename"
                )

            p = Path(td) / filename

            content = await f.read()
            p.write_bytes(content)

            paths[filename] = p

        results = processor.process(paths, data, caller)

    completed = sum(
        r.processing_status == "COMPLETED"
        for r in results
    )

    failed = len(results) - completed

    return {
        "batch_id": data.batch_id,
        "summary": {
            "total": len(results),
            "completed": completed,
            "failed": failed
        },
        "results": [
            r.model_dump(mode="json")
            for r in results
        ]
    }