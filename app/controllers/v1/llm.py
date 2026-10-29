from fastapi import Depends, Request
from loguru import logger

from app.controllers import base
from app.controllers.v1.base import new_router
from app.models.exception import HttpException
from app.models.schema import (
    VideoScriptRequest,
    VideoScriptResponse,
    VideoSocialMetadataRequest,
    VideoSocialMetadataResponse,
    VideoTermsRequest,
    VideoTermsResponse,
)
from app.services import llm
from app.utils import utils

router = new_router(dependencies=[Depends(base.verify_token)])


@router.post(
    "/scripts",
    response_model=VideoScriptResponse,
    summary="Create a script for the video",
)
def generate_video_script(request: Request, body: VideoScriptRequest):
    request_id = (
        base.get_task_id(request)
        if request and hasattr(request, "headers")
        else "script-gen"
    )
    try:
        video_script = llm.generate_script(
            video_subject=body.video_subject,
            language=body.video_language,
            paragraph_number=body.paragraph_number,
            video_script_prompt=body.video_script_prompt,
            custom_system_prompt=body.custom_system_prompt,
        )
        if (
            not video_script
            or not isinstance(video_script, str)
            or video_script.startswith("Error:")
            or "Error:" in video_script
        ):
            raise HttpException(
                task_id=request_id,
                status_code=500,
                message=f"{request_id}: failed to generate video script",
            )
        response = {"video_script": str(video_script).strip()}
        return utils.get_response(200, response)
    except HttpException:
        raise
    except Exception as exc:
        logger.error(
            f"failed to generate video script, request_id: {request_id}, error: {str(exc)}"
        )
        raise HttpException(
            task_id=request_id,
            status_code=500,
            message=f"{request_id}: failed to generate video script",
        )


@router.post(
    "/terms",
    response_model=VideoTermsResponse,
    summary="Generate video terms based on the video script",
)
def generate_video_terms(request: Request, body: VideoTermsRequest):
    request_id = (
        base.get_task_id(request)
        if request and hasattr(request, "headers")
        else "terms-gen"
    )
    try:
        video_terms = llm.generate_terms(
            video_subject=body.video_subject,
            video_script=body.video_script,
            amount=body.amount,
            match_script_order=body.match_materials_to_script,
        )
        if not isinstance(video_terms, list) or not video_terms:
            raise HttpException(
                task_id=request_id,
                status_code=500,
                message=f"{request_id}: failed to generate video terms",
            )
        sanitized_terms = [
            str(term).strip()
            for term in video_terms
            if isinstance(term, str)
            and term.strip()
            and not term.startswith("Error:")
            and "Error:" not in term
        ]
        if not sanitized_terms:
            raise HttpException(
                task_id=request_id,
                status_code=500,
                message=f"{request_id}: failed to generate video terms",
            )
        response = {"video_terms": sanitized_terms}
        return utils.get_response(200, response)
    except HttpException:
        raise
    except Exception as exc:
        logger.error(
            f"failed to generate video terms, request_id: {request_id}, error: {str(exc)}"
        )
        raise HttpException(
            task_id=request_id,
            status_code=500,
            message=f"{request_id}: failed to generate video terms",
        )


@router.post(
    "/social-metadata",
    response_model=VideoSocialMetadataResponse,
    summary="Generate social publishing metadata",
)
def generate_video_social_metadata(
    request: Request, body: VideoSocialMetadataRequest
):
    request_id = (
        base.get_task_id(request)
        if request and hasattr(request, "headers")
        else "social-meta"
    )
    try:
        metadata = llm.generate_social_metadata(
            video_subject=body.video_subject,
            video_script=body.video_script,
            language=body.language,
            platform=body.platform,
        )
        if not isinstance(metadata, dict) or not metadata:
            raise HttpException(
                task_id=request_id,
                status_code=500,
                message=f"{request_id}: failed to generate social metadata",
            )
        sanitized_metadata = {
            str(k): (
                [str(item) for item in v if isinstance(item, str) and not item.startswith("Error:")]
                if isinstance(v, list)
                else str(v)
            )
            for k, v in metadata.items()
            if not str(k).startswith("Error:") and not str(v).startswith("Error:")
        }
        return utils.get_response(200, sanitized_metadata)
    except HttpException:
        raise
    except Exception as exc:
        logger.error(
            f"failed to generate social metadata, request_id: {request_id}, error: {str(exc)}"
        )
        raise HttpException(
            task_id=request_id,
            status_code=500,
            message=f"{request_id}: failed to generate social metadata",
        )
