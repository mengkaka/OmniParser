from util.utils import (
    get_som_labeled_img,
    get_caption_model_processor,
    get_yolo_model,
    check_ocr_box,
    resolve_torch_device,
)
from PIL import Image
import io
import base64
from typing import Dict, Optional, Any, Tuple, Literal

ResponseMode = Literal["image", "json", "all"]


def resolve_output_flags(
    response_mode: ResponseMode = "all",
    return_parsed_content: bool = True,
) -> Tuple[bool, bool, bool]:
    """
    Map API params to pipeline flags.

    Returns:
        return_som_image: draw and encode annotated PNG
        use_local_semantics: run Florence2 icon captions
        include_parsed_in_response: include parsed_content_list in JSON response
    """
    if response_mode == "image":
        # Only annotated image; ignore return_parsed_content.
        return True, False, False
    if response_mode == "json":
        return False, return_parsed_content, True
    # all
    return True, return_parsed_content, True


class Omniparser(object):
    def __init__(self, config: Dict):
        self.config = config
        device = resolve_torch_device(config.get("device", "auto"))
        self.device = device

        self.som_model = get_yolo_model(model_path=config["som_model_path"])
        self.caption_model_processor = get_caption_model_processor(
            model_name=config["caption_model_name"],
            model_name_or_path=config["caption_model_path"],
            device=device,
        )
        print(f"Omniparser initialized (device={device})")

    def parse(
        self,
        image_base64: str,
        *,
        response_mode: ResponseMode = "all",
        return_parsed_content: bool = True,
        box_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        return_som_image, use_local_semantics, include_parsed = resolve_output_flags(
            response_mode, return_parsed_content
        )

        image_bytes = base64.b64decode(image_base64)
        image = Image.open(io.BytesIO(image_bytes))
        print(
            "image size:",
            image.size,
            f"response_mode={response_mode}",
            f"use_local_semantics={use_local_semantics}",
        )

        box_overlay_ratio = max(image.size) / 3200
        draw_bbox_config = {
            "text_scale": 0.8 * box_overlay_ratio,
            "text_thickness": max(int(2 * box_overlay_ratio), 1),
            "text_padding": max(int(3 * box_overlay_ratio), 1),
            "thickness": max(int(3 * box_overlay_ratio), 1),
        }

        bt = box_threshold if box_threshold is not None else self.config["BOX_TRESHOLD"]
        iou = iou_threshold if iou_threshold is not None else self.config.get("iou_threshold", 0.7)

        (text, ocr_bbox), _ = check_ocr_box(
            image,
            display_img=False,
            output_bb_format="xyxy",
            easyocr_args={"text_threshold": 0.8},
            use_paddleocr=False,
        )

        som_image, _label_coordinates, parsed_content_list = get_som_labeled_img(
            image,
            self.som_model,
            BOX_TRESHOLD=bt,
            output_coord_in_ratio=True,
            ocr_bbox=ocr_bbox,
            draw_bbox_config=draw_bbox_config,
            caption_model_processor=self.caption_model_processor,
            ocr_text=text,
            use_local_semantics=use_local_semantics,
            iou_threshold=iou,
            scale_img=False,
            batch_size=128,
            return_som_image=return_som_image,
        )

        result: Dict[str, Any] = {}
        if return_som_image and som_image:
            result["som_image_base64"] = som_image
        if include_parsed:
            result["parsed_content_list"] = parsed_content_list
        return result
