'''
python -m omnitool.omniparserserver.omniparserserver \
  --som_model_path weights/icon_detect/model.pt \
  --caption_model_name florence2 \
  --caption_model_path weights/icon_caption_florence \
  --device auto --BOX_TRESHOLD 0.05
'''

import sys
import os
import time
from typing import Optional, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import argparse
import uvicorn

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)
from util.omniparser import Omniparser

ResponseMode = Literal["image", "json", "all"]


def parse_arguments():
    parser = argparse.ArgumentParser(description="Omniparser API")
    parser.add_argument("--som_model_path", type=str, default="../../weights/icon_detect/model.pt", help="Path to the som model")
    parser.add_argument("--caption_model_name", type=str, default="florence2", help="Name of the caption model")
    parser.add_argument("--caption_model_path", type=str, default="../../weights/icon_caption_florence", help="Path to the caption model")
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        help="Inference device: auto (cuda>mps>cpu), cpu, cuda, mps",
    )
    parser.add_argument("--BOX_TRESHOLD", type=float, default=0.05, help="Default icon detection confidence threshold")
    parser.add_argument("--iou_threshold", type=float, default=0.7, help="Default IOU threshold for merging overlapping boxes")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host for the API (0.0.0.0 = LAN accessible)")
    parser.add_argument("--port", type=int, default=8000, help="Port for the API")
    return parser.parse_args()


args = parse_arguments()
config = vars(args)

app = FastAPI()
omniparser = Omniparser(config)


class ParseRequest(BaseModel):
    base64_image: str = Field(..., description="PNG/JPEG as standard base64 (no data: URL prefix)")
    response_mode: ResponseMode = Field(
        "all",
        description=(
            "Response mode: "
            "'all' = image + JSON (default); "
            "'image' = annotated image only (ignores return_parsed_content); "
            "'json' = JSON only"
        ),
    )
    return_parsed_content: bool = Field(
        True,
        description=(
            "When response_mode is 'json' or 'all': true = run Florence2 icon captions; "
            "false = OCR + boxes only, no icon semantics. Ignored when response_mode is 'image'."
        ),
    )
    box_threshold: Optional[float] = Field(
        None,
        ge=0.01,
        le=1.0,
        description="Icon detect confidence; higher=fewer icons. Omitted = server default 0.05",
    )
    iou_threshold: Optional[float] = Field(
        None,
        ge=0.01,
        le=1.0,
        description="Overlap merge threshold; higher=fewer icons. Omitted = server default 0.7",
    )


@app.post("/parse/")
async def parse(parse_request: ParseRequest):
    print("start parsing...")
    start = time.time()
    try:
        payload = omniparser.parse(
            parse_request.base64_image,
            response_mode=parse_request.response_mode,
            return_parsed_content=parse_request.return_parsed_content,
            box_threshold=parse_request.box_threshold,
            iou_threshold=parse_request.iou_threshold,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    latency = time.time() - start
    print("time:", latency)
    return {"latency": latency, **payload}


@app.get("/probe/")
async def probe():
    return {
        "message": "Omniparser API ready",
        "device": omniparser.device,
        "box_threshold": config["BOX_TRESHOLD"],
        "iou_threshold": config["iou_threshold"],
    }


if __name__ == "__main__":
    uvicorn.run(app, host=args.host, port=args.port, reload=False)
